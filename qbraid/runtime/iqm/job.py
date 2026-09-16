# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""IQM job implementation and measurement-result conversion."""

# pylint:disable=invalid-name

from __future__ import annotations

import re
import warnings
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from qbraid_core._import import LazyLoader

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.iqm.exceptions import IQMJobError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import BatchResult, Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    import iqm.iqm_client
    import iqm.qiskit_iqm.qiskit_to_iqm

    import qbraid.runtime.iqm

qbraid_rt_iqm = LazyLoader("qbraid_rt_iqm", globals(), "qbraid.runtime.iqm")
iqm_qiskit: iqm.qiskit_iqm.qiskit_to_iqm = LazyLoader(
    "iqm_qiskit",
    globals(),
    "iqm.qiskit_iqm.qiskit_to_iqm",
)


_QISKIT_KEY_RE = re.compile(r".+_(?P<creg_len>\d+)_(?P<creg_idx>\d+)_(?P<clbit_idx>\d+)")


@dataclass(frozen=True)
class _MeasurementKey:
    """Where one IQM measurement result lands in the classical register layout."""

    creg_idx: int
    creg_len: int
    clbit_idx: int


def _parse_measurement_key(key: str, values, register_index: int) -> _MeasurementKey:
    """Locate an IQM measurement key in the classical register layout.

    Circuits serialized from Qiskit carry ``<creg>_<len>_<creg idx>_<bit idx>`` keys,
    which name one exact bit. Circuits from any other frontend carry whatever key the
    user wrote, so each key becomes its own register, as wide as the measured locus.
    Parsed here rather than via ``iqm.qiskit_iqm`` so decoding results never needs Qiskit.
    """
    match = _QISKIT_KEY_RE.fullmatch(key)
    if match:
        return _MeasurementKey(
            creg_idx=int(match.group("creg_idx")),
            creg_len=int(match.group("creg_len")),
            clbit_idx=int(match.group("clbit_idx")),
        )
    shape = np.asarray(values, dtype=int).shape
    return _MeasurementKey(register_index, shape[1] if len(shape) > 1 else 1, 0)


def _format_measurement_memory(
    measurement_results: iqm.iqm_client.CircuitMeasurementResults,
) -> list[str]:
    """Convert one IQM circuit result into Qiskit's classical-register layout.

    Measurement keys encode ``<register>_<length>_<register index>_<bit index>``.
    For example, ``{"c_2_0_0": [[1], [0]], "c_2_0_1": [[0], [1]]}``
    becomes ``["01", "10"]``: one little-endian bitstring per shot.

    Args:
        measurement_results: Results keyed by IQM measurement key.
    Returns:
        One Qiskit-style memory string per shot.

    Raises:
        ValueError: If a result has the wrong shape or measurement keys contain
            inconsistent shot counts.
    """
    formatted_results: dict[int, np.ndarray] = {}
    shot_count: int | None = None

    for register_index, (key, values) in enumerate(measurement_results.items()):
        measurement_key = _parse_measurement_key(key, values, register_index)
        result_array = np.asarray(values, dtype=int)
        current_shots = len(result_array)

        if shot_count is None:
            shot_count = current_shots
        elif current_shots != shot_count:
            raise ValueError(
                "Inconsistent number of shots in measurement results: "
                f"expected {shot_count} but got {current_shots} for {measurement_key}"
            )

        if current_shots == 0:
            warnings.warn(
                "Received measurement results containing zero shots. "
                "In case you are using non-default heralding mode, this could be "
                "because of bad calibration.",
                stacklevel=2,
            )
            result_array = np.array([], dtype=int)
        else:
            if result_array.ndim != 2:
                raise ValueError(
                    f"Measurement result {measurement_key} has the wrong shape "
                    f"{result_array.shape}, expected (*, N)"
                )

        classical_register = formatted_results.setdefault(
            measurement_key.creg_idx,
            np.zeros((current_shots, measurement_key.creg_len), dtype=int),
        )
        width = result_array.shape[1]
        classical_register[:, measurement_key.clbit_idx : measurement_key.clbit_idx + width] = (
            result_array
        )

    resolved_shots = shot_count or 0
    return [
        " ".join(
            "".join(map(str, classical_register[shot, :]))
            for _, classical_register in sorted(formatted_results.items())
        )[::-1]
        for shot in range(resolved_shots)
    ]


def _format_measurement_results(
    measurement_results: iqm.iqm_client.CircuitMeasurementResults,
) -> tuple[list[str], np.ndarray, dict[str, int]]:
    """Build qBraid memory, shot-array, and count views for one IQM circuit result."""
    memory = _format_measurement_memory(measurement_results)
    bitstrings = [item.replace(" ", "") for item in memory]
    measurements = (
        np.array([[int(bit) for bit in bitstring] for bitstring in bitstrings], dtype=int)
        if bitstrings
        else np.empty((0, 0), dtype=int)
    )
    counts = dict(sorted(Counter(bitstrings).items()))
    return memory, measurements, counts


_JOB_STATUS = {
    "waiting": JobStatus.QUEUED,
    "processing": JobStatus.RUNNING,
    "completed": JobStatus.COMPLETED,
    "failed": JobStatus.FAILED,
    "cancelled": JobStatus.CANCELLED,
}


class IQMJob(QuantumJob):
    """IQM job class."""

    def __init__(
        self,
        job_id: str,
        session: qbraid.runtime.iqm.IQMSession | None = None,
        job: iqm.iqm_client.CircuitJob | None = None,
        **kwargs,
    ):
        super().__init__(job_id=job_id, **kwargs)
        self._session = session or qbraid_rt_iqm.IQMSession()
        self._job = job

    @property
    def session(self) -> qbraid.runtime.iqm.IQMSession:
        """Return the IQM session."""
        return self._session

    @staticmethod
    def _map_status(status: str) -> JobStatus:
        """Convert an IQM job status to a qBraid job status."""
        try:
            return _JOB_STATUS[status.lower()]
        except KeyError as err:
            raise IQMJobError(
                f"Unrecognized IQM job status '{status}'. This usually means IQM added a "
                "status qBraid does not map yet."
            ) from err

    def _get_job(self, refresh: bool = False) -> iqm.iqm_client.CircuitJob:
        if refresh or self._job is None:
            self._job = self.session.get_job(str(self.id))
        return self._job

    @staticmethod
    def _stringify_many(items: Sequence[object]) -> list[str]:
        return [str(item) for item in items]

    def _resolve_device_id(self) -> str:
        """Resolve the device identifier for the current job."""
        cached_device_id = self._cache_metadata.get("device_id")
        if isinstance(cached_device_id, str):
            return cached_device_id

        if self._device is not None:
            device_id = self.device.id
            self._cache_metadata["device_id"] = device_id
            return device_id

        device_id = self.session.quantum_computer or self.session.url
        self._cache_metadata["device_id"] = device_id
        return device_id

    def _terminal_status(self) -> JobStatus | None:
        """Return a known terminal status without making a server request."""
        cached_status = self._cache_metadata.get("status")
        if isinstance(cached_status, JobStatus) and cached_status in JobStatus.terminal_states():
            return cached_status

        if self._job is not None:
            status = self._map_status(self._job.data.status.value)
            if status in JobStatus.terminal_states():
                self._cache_metadata["status"] = status
                return status
        return None

    def status(self) -> JobStatus:
        """Return the current status of the IQM job."""
        if terminal_status := self._terminal_status():
            return terminal_status

        job = self._get_job(refresh=True)
        status = self._map_status(job.data.status.value)
        self._cache_metadata["status"] = status
        return status

    def metadata(self) -> dict[str, object]:
        """Store and return metadata for the IQM job."""
        job = self._get_job(refresh=self._terminal_status() is None)
        job_data = job.data
        messages = self._stringify_many(job_data.messages)
        errors = self._stringify_many(job_data.errors)
        compilation = job_data.compilation

        self._cache_metadata.update(
            {
                "device_id": self._resolve_device_id(),
                "messages": messages,
                "errors": errors,
                "queue_position": job_data.queue_position,
                "timeline": job_data.timeline,
                "status": self._map_status(job_data.status.value),
                "calibration_set_id": (
                    compilation.calibration_set_id if compilation is not None else None
                ),
            }
        )
        return self._cache_metadata

    def queue_position(self) -> int | None:
        """Return the job's position in the IQM queue, or ``None`` once it has started."""
        return self._get_job(refresh=self._terminal_status() is None).data.queue_position

    def cancel(self) -> None:
        """Cancel the IQM job."""
        self.session.cancel_job(str(self.id))

    def result(  # type: ignore[override]  # batch submissions return a BatchResult
        self,
    ) -> Result[GateModelResultData] | BatchResult[GateModelResultData]:
        """Return the result of the IQM job."""
        self.wait_for_final_state()
        job = self._get_job()
        job_data = job.data
        status_value = job_data.status.value
        status = self._map_status(status_value)

        if status != JobStatus.COMPLETED:
            messages = self._stringify_many(job_data.messages)
            errors = self._stringify_many(job_data.errors)
            reason = "; ".join(errors or messages) or "No additional error details returned by IQM."
            raise IQMJobError(f"Job {self.id} finished with status '{status_value}': {reason}")

        measurement_batch = self.session.get_job_measurements(str(self.id))
        formatted_results = [
            _format_measurement_results(measurements) for measurements in measurement_batch
        ]

        compilation = job_data.compilation
        device_id = self._resolve_device_id()
        details = {
            "status": status,
            "messages": self._stringify_many(job_data.messages),
            "errors": self._stringify_many(job_data.errors),
            "queue_position": job_data.queue_position,
            "timeline": job_data.timeline,
            "calibration_set_id": (
                compilation.calibration_set_id if compilation is not None else None
            ),
        }
        results = [
            Result(
                device_id=device_id,
                job_id=self.id,
                success=True,
                data=GateModelResultData(
                    measurement_counts=counts,
                    measurements=shot_data,
                ),
                **details,
            )
            for _, shot_data, counts in formatted_results
        ]

        if len(results) == 1:
            return results[0]

        return BatchResult(
            device_id=device_id,
            job_id=self.id,
            success=True,
            results=results,
            **details,
        )

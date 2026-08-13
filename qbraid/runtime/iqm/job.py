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

import warnings
from collections import Counter
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from qbraid_core._import import LazyLoader

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import BatchResult, Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    import iqm.iqm_client
    import iqm.qiskit_iqm.qiskit_to_iqm

    import qbraid.runtime.iqm

qbraid_rt_iqm: qbraid.runtime.iqm = LazyLoader("qbraid_rt_iqm", globals(), "qbraid.runtime.iqm")
iqm_qiskit: iqm.qiskit_iqm.qiskit_to_iqm = LazyLoader(
    "iqm_qiskit",
    globals(),
    "iqm.qiskit_iqm.qiskit_to_iqm",
)


def _format_measurement_memory(
    measurement_results: iqm.iqm_client.CircuitMeasurementResults,
    requested_shots: int,
    expect_exact_shots: bool = True,
) -> list[str]:
    """Convert one IQM circuit result into Qiskit's classical-register layout.

    Measurement keys encode ``<register>_<length>_<register index>_<bit index>``.
    For example, ``{"c_2_0_0": [[1], [0]], "c_2_0_1": [[0], [1]]}``
    becomes ``["01", "10"]``: one little-endian bitstring per shot.

    Args:
        measurement_results: Results keyed by IQM measurement key.
        requested_shots: Number of shots requested at submission time.
        expect_exact_shots: Whether every key must contain exactly ``requested_shots`` rows.

    Returns:
        One Qiskit-style memory string per shot.

    Raises:
        ValueError: If a result has the wrong shape or measurement keys contain
            inconsistent shot counts.
    """
    formatted_results: dict[int, np.ndarray] = {}
    shot_count = requested_shots if expect_exact_shots else None

    for key, values in measurement_results.items():
        measurement_key = iqm_qiskit.MeasurementKey.from_string(key)
        result_array = np.asarray(values, dtype=int)
        current_shots = len(result_array)

        if expect_exact_shots:
            if current_shots != requested_shots:
                raise ValueError(
                    f"Expected {requested_shots} shots but got {current_shots} "
                    f"for measurement result {measurement_key}"
                )
        elif shot_count is None:
            shot_count = current_shots
        elif current_shots != shot_count:
            raise ValueError(
                "Inconsistent number of shots in measurement results: "
                f"expected {shot_count} but got {current_shots} for {measurement_key}"
            )

        if current_shots == 0 and not expect_exact_shots:
            warnings.warn(
                "Received measurement results containing zero shots. "
                "In case you are using non-default heralding mode, this could be "
                "because of bad calibration.",
                stacklevel=2,
            )
            result_array = np.array([], dtype=int)
        else:
            if result_array.ndim != 2 or result_array.shape[1] != 1:
                raise ValueError(
                    f"Measurement result {measurement_key} has the wrong shape "
                    f"{result_array.shape}, expected (*, 1)"
                )
            result_array = result_array[:, 0]

        classical_register = formatted_results.setdefault(
            measurement_key.creg_idx,
            np.zeros((current_shots, measurement_key.creg_len), dtype=int),
        )
        classical_register[:, measurement_key.clbit_idx] = result_array

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
    memory = _format_measurement_memory(
        measurement_results,
        requested_shots=0,
        expect_exact_shots=False,
    )
    bitstrings = [item.replace(" ", "") for item in memory]
    measurements = (
        np.array([[int(bit) for bit in bitstring] for bitstring in bitstrings], dtype=int)
        if bitstrings
        else np.empty((0, 0), dtype=int)
    )
    counts = dict(sorted(Counter(bitstrings).items()))
    return memory, measurements, counts


class IQMJobError(QbraidRuntimeError):
    """Class for errors raised while processing an IQM job."""


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
        status_map = {
            "waiting": JobStatus.QUEUED,
            "processing": JobStatus.RUNNING,
            "completed": JobStatus.COMPLETED,
            "failed": JobStatus.FAILED,
            "cancelled": JobStatus.CANCELLED,
        }
        return status_map.get(status.lower(), JobStatus.UNKNOWN)

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

    def cancel(self) -> None:
        """Cancel the IQM job."""
        self.session.cancel_job(self.id)

    def result(
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
            details = (
                "; ".join(errors or messages) or "No additional error details returned by IQM."
            )
            raise IQMJobError(f"Job {self.id} finished with status '{status_value}': {details}")

        measurement_batch = self.session.get_job_measurements(self.id)
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

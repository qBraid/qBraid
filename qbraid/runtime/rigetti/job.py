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

# pylint: disable=no-name-in-module

# The above disable is necessary because the qcs_sdk.* modules load from Rust extension bindings
# (__file__ is None for submodules), so pylint/astroid can’t reliably introspect exported names
# and emits E0611 false positives.
#
"""
Module defining Rigetti job class

"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Optional

import numpy as np
from qcs_sdk.qpu import QPUResultData, ReadoutValues
from qcs_sdk.qpu.api import QpuApiError, cancel_job, retrieve_results

from qbraid.runtime import JobStateError
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .device import RigettiDevice


class RigettiJobError(QbraidRuntimeError):
    """Class for errors raised while processing an Rigetti job."""


class RigettiJob(QuantumJob):
    """Rigetti job class."""

    def __init__(
        self,
        job_id: str | int,
        device: RigettiDevice,
        num_shots: int = 1,
        ro_sources: Optional[dict] = None,
        **kwargs: Any,
    ):
        super().__init__(job_id=job_id, device=device, **kwargs)
        self._num_shots = num_shots
        self._ro_sources = ro_sources or {}
        self._status = JobStatus.INITIALIZING
        self._cached_results = None

    @property
    def _client(self):
        return self._device._qcs_client

    def status(self) -> JobStatus:
        """Return the current status of the Rigetti job.

        The QCS SDK does not expose a job-status endpoint. Instead,
        ``retrieve_results`` blocks until the job completes. This method
        attempts a retrieval to detect completion or failure and caches
        the result for later use by ``get_result()``.
        """
        if self._status in JobStatus.terminal_states():
            return self._status

        try:
            # TODO: Figure out what status enums are returned in the
            # qcs_sdk when we query the details of the job, and
            # map those to the JobStatus enums.
            # Currently, there is no way to know if the job is queued,
            # or running, or in some other non-terminal state
            self._cached_results = retrieve_results(
                job_id=str(self.id),
                quantum_processor_id=self._device.id,
                client=self._client,
            )
            self._status = JobStatus.COMPLETED
        except QpuApiError as err:
            if "timeout" in str(err).lower():
                logger.info("Retrieve timed out for job %s; job may still be running.", self.id)
            else:
                self._status = JobStatus.FAILED

        return self._status

    def cancel(self) -> None:
        """Cancel the Rigetti job.
        We set the job status internally in the cancel job because
        the QCS API does not return status updates for job cancellation.
        """
        if self._status in JobStatus.terminal_states():
            raise JobStateError(f"Cannot cancel job {self.id} in terminal state {self._status}.")
        previous_status = self._status
        self._status = JobStatus.CANCELLING
        try:
            logger.info(
                "Attempting to cancel Rigetti job %s on device %s",
                self.id,
                self._device.id,
            )
            cancel_job(
                job_id=str(self.id),
                quantum_processor_id=self._device.id,
                client=self._client,
            )
        except QpuApiError as exc:
            self._status = previous_status
            raise RigettiJobError(
                "Failed to cancel the QPU job. "
                "Cancellation is not guaranteed, as it "
                "is based on job state at the time of cancellation."
            ) from exc
        self._status = JobStatus.CANCELLED
        logger.info(
            "Successfully cancelled Rigetti job %s on device %s",
            self.id,
            self._device.id,
        )

    def _build_register_map(self, execution_results):
        """Build a ``RegisterMap`` from raw execution results and ro_sources.

        Constructs a ``QPUResultData`` object and calls ``to_register_map()``
        which handles qubit ordering and register grouping internally.
        """
        readout_values = {
            key: ReadoutValues(value.data) for key, value in execution_results.buffers.items()
        }
        qpu_result_data = QPUResultData(
            mappings=dict(self._ro_sources),
            readout_values=readout_values,
            memory_values=execution_results.memory,
        )
        return qpu_result_data.to_register_map()

    def _parse_results(self, execution_results) -> GateModelResultData:
        """Parse raw execution results into GateModelResultData.

        Uses ``QPUResultData.to_register_map()`` to convert raw buffers
        into per-register numpy arrays, then extracts the user-declared
        registers and builds measurement count strings.
        """
        register_map = self._build_register_map(execution_results)

        # Identify user-declared register names from ro_sources
        # e.g. "ro[0]" -> "ro", "aux[1]" -> "aux"
        declared_registers = set()
        for mem_ref in self._ro_sources:
            match = re.match(r"^(.+)\[\d+\]$", mem_ref)
            if match:
                declared_registers.add(match.group(1))

        if not declared_registers:
            raise RigettiJobError(
                "No declared registers found in ro_sources. "
                f"ro_sources keys: {list(self._ro_sources.keys())}"
            )

        # Concatenate declared registers in sorted order into measurement bitstrings
        # Each register matrix has shape (num_shots, num_bits_in_register)
        register_arrays = []
        for reg_name in sorted(declared_registers):
            matrix = register_map.get_register_matrix(reg_name)
            if matrix is None:
                continue
            register_arrays.append(matrix.to_ndarray().astype(int))

        if not register_arrays:
            raise RigettiJobError(
                f"No data found for declared registers {declared_registers} "
                f"in register map keys: {list(register_map.keys())}"
            )

        # Horizontally stack all register arrays: (num_shots, total_bits)
        all_bits = np.hstack(register_arrays)

        measurements = []
        for row in all_bits:
            measurements.append("".join(str(b) for b in row))

        counts = {m: measurements.count(m) for m in set(measurements)}
        return GateModelResultData(measurement_counts=counts)

    def result(self, timeout: Optional[int] = None) -> Result:
        """Return the result of the Rigetti job.

        Raises:
            RigettiJobError: If the job result cannot be retrieved or parsed.
        """
        self.wait_for_final_state(timeout=timeout)
        if self._cached_results is None:
            self._cached_results = retrieve_results(
                job_id=str(self.id),
                quantum_processor_id=self._device.id,
                client=self._client,
            )
        result_data = self._parse_results(self._cached_results)

        self._status = JobStatus.COMPLETED
        return Result[GateModelResultData](
            device_id=self._device.id,
            job_id=self.id,
            success=True,
            data=result_data,
        )

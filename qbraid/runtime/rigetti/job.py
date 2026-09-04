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

import re
from typing import TYPE_CHECKING, Any

import numpy as np
from qcs_sdk import RegisterMap
from qcs_sdk.client import QCSClient
from qcs_sdk.qpu import QPUResultData, ReadoutValues
from qcs_sdk.qpu.api import (
    ExecutionOptions,
    ExecutionResults,
    QpuApiError,
    cancel_job,
    retrieve_results,
)

from qbraid._logging import logger
from qbraid.runtime import JobStateError
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    from .device import RigettiDevice


class RigettiJobError(QbraidRuntimeError):
    """Class for errors raised while processing an Rigetti job."""


class RigettiJob(QuantumJob):
    """Rigetti job class."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        job_id: str,
        num_shots: int,
        device: RigettiDevice | None = None,
        qcs_client: QCSClient | None = None,
        ro_sources: dict[str, str] | None = None,
        execution_options: ExecutionOptions | None = None,
        compiled_program: str | None = None,
        **kwargs: Any,
    ):
        """Initialize a RigettiJob.

        Args:
            job_id: The QCS job identifier returned by ``qpu_submit`` (a string).
            num_shots: Required. Number of shots that the job was submitted
                with; used downstream by parsers and result formatting.
            device: The originating ``RigettiDevice``. May be ``None`` when
                rehydrating a job by ID alone, in which case ``qcs_client``
                must be provided.
            qcs_client: An authenticated ``QCSClient``. When ``None``, the
                ``client`` property falls back to ``device.client``.
            ro_sources: Mapping from declared memory references (e.g.
                ``"ro[0]"``) to the readout buffer keys returned by
                ``ExecutionResults.buffers``. Sourced from
                ``TranslationResult.ro_sources``.
            execution_options: The ``ExecutionOptions`` used at submission
                time. Reused for ``cancel`` and ``retrieve_results`` so the
                job hits the same gRPC endpoint that accepted it.
            compiled_program: The native Quil program produced by quilc that
                was submitted for translation and execution. ``None`` when
                rehydrating a job by ID, since compilation output is not
                retrievable from QCS after submission.
        """
        super().__init__(job_id=job_id, device=device, **kwargs)
        self._qcs_client = qcs_client
        self._num_shots = num_shots
        self._ro_sources = ro_sources or {}
        self._execution_options = execution_options
        self._compiled_program = compiled_program
        self._status = JobStatus.INITIALIZING
        self._status_message: str | None = None
        self._cached_results: ExecutionResults | None = None

    @property
    def client(self) -> QCSClient:
        """Return the authenticated ``QCSClient`` used by this job.

        Prefers the explicit client passed at construction, falling back to
        the device's client. Raises ``RigettiJobError`` if neither is set.
        """
        if self._qcs_client is not None:
            return self._qcs_client
        if self._device is not None:
            return self._device.client
        raise RigettiJobError(
            f"RigettiJob {self.id} has no QCSClient: pass qcs_client= or device=."
        )

    @property
    def compiled_program(self) -> str | None:
        """The native Quil program produced by quilc for this job, if known.

        Reveals the physical qubits selected and the final rewiring chosen by
        the compiler — information not recoverable from measurement counts.
        ``None`` for jobs rehydrated by ID (e.g. on a later status poll),
        since QCS does not expose compilation output after submission.
        """
        return self._compiled_program

    @property
    def status_message(self) -> str | None:
        """Failure detail from the most recent status poll, if any.

        Unlike ``JobStatus.status_message`` — which lives on the shared enum
        member and can be overwritten by any concurrently polled job — this
        value is per-instance and safe to read after ``status()`` returns.
        """
        return self._status_message

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
                quantum_processor_id=self.device.id,
                client=self.client,
                execution_options=self._execution_options,
            )
            self._status = JobStatus.COMPLETED
        except QpuApiError as err:
            if "timeout" in str(err).lower():
                logger.info("Retrieve timed out for job %s; job may still be running.", self.id)
            else:
                logger.error("Result retrieval failed for job %s: %s", self.id, err)
                self._status_message = str(err)
                status = JobStatus.FAILED
                status.set_status_message(str(err))
                self._status = status

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
                self.device.id,
            )
            cancel_job(
                job_id=str(self.id),
                quantum_processor_id=self.device.id,
                client=self.client,
                execution_options=self._execution_options,
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
            self.device.id,
        )

    def _build_register_map(self, execution_results: ExecutionResults) -> RegisterMap:
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

    _DECLARE_PATTERN = re.compile(r"^\s*DECLARE\s+(\S+)\s", re.MULTILINE)

    def _register_order(self, declared_registers: set[str]) -> list[str]:
        """Return the declared registers in the program's DECLARE order.

        ``ro_sources`` cannot supply this order: it arrives in Rust HashMap
        iteration order, and concatenating registers in any order other than
        the program's silently corrupts every bitstring (#1308). Refuse to
        guess when the submitted program is unavailable.
        """
        if len(declared_registers) == 1:
            return list(declared_registers)
        if self._compiled_program is None:
            raise RigettiJobError(
                f"Job {self.id} declares multiple readout registers "
                f"({sorted(declared_registers)}), but the submitted program is not "
                "available to establish their declaration order (jobs rehydrated by "
                "ID do not retain it). Refusing to guess an order, since a wrong "
                "one corrupts every returned bitstring. Pass the submitted program "
                "as compiled_program= to recover the order."
            )
        order: list[str] = []
        for name in self._DECLARE_PATTERN.findall(self._compiled_program):
            if name in declared_registers and name not in order:
                order.append(name)
        missing = declared_registers.difference(order)
        if missing:
            raise RigettiJobError(
                f"Registers {sorted(missing)} from ro_sources have no DECLARE "
                "statement in the submitted program; cannot establish readout order."
            )
        return order

    def _parse_results(self, execution_results: ExecutionResults) -> GateModelResultData:
        """Parse raw execution results into GateModelResultData.

        Uses ``QPUResultData.to_register_map()`` to convert raw buffers
        into per-register numpy arrays, then extracts the user-declared
        registers and builds measurement count strings. Registers are
        concatenated in the program's DECLARE order.
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

        # Each register matrix has shape (num_shots, num_bits_in_register)
        register_arrays = []
        for reg_name in self._register_order(declared_registers):
            matrix = register_map.get_register_matrix(reg_name)
            if matrix is None:
                raise RigettiJobError(
                    f"No data returned for declared register '{reg_name}' "
                    f"(register map keys: {list(register_map.keys())})."
                )
            register_arrays.append(matrix.to_ndarray().astype(int))

        # Horizontally stack all register arrays: (num_shots, total_bits)
        all_bits = np.hstack(register_arrays)

        measurements = []
        for row in all_bits:
            measurements.append("".join(str(b) for b in row))

        counts = {m: measurements.count(m) for m in set(measurements)}
        return GateModelResultData(measurement_counts=counts)

    def result(self, timeout: int | None = None) -> Result[GateModelResultData]:
        """Return the result of the Rigetti job.

        Raises:
            RigettiJobError: If the job result cannot be retrieved or parsed.
        """
        self.wait_for_final_state(timeout=timeout)
        if self._cached_results is None:
            self._cached_results = retrieve_results(
                job_id=str(self.id),
                quantum_processor_id=self.device.id,
                client=self.client,
                execution_options=self._execution_options,
            )

        try:
            result_data = self._parse_results(self._cached_results)
        except RigettiJobError:
            # Already a RigettiJobError; let it propagate unchanged so the
            # original message (e.g. "No declared registers") is preserved.
            raise
        except Exception as exc:
            # Wrap any other parser-side failure so the docstring's
            # "Raises: RigettiJobError" contract holds.
            raise RigettiJobError(f"Failed to parse execution results for job {self.id}.") from exc

        self._status = JobStatus.COMPLETED
        extra_details: dict[str, Any] = {}
        if self._compiled_program is not None:
            extra_details["compiled_program"] = self._compiled_program
        return Result[GateModelResultData](
            device_id=self.device.id,
            job_id=self.id,
            success=True,
            data=result_data,
            execution_duration_microseconds=(self._cached_results.execution_duration_microseconds),
            ro_sources=dict(self._ro_sources),
            **extra_details,
        )

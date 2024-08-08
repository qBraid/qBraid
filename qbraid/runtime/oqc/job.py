# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for OQC job class.

"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.job import QuantumJob

from .result import OQCJobResult

if TYPE_CHECKING:
    from qcaas_client.client import OQCClient, QPUTaskErrors

RESULTS_FORMAT = {
    2: "raw",
    3: "binary",
}

METRICS = {
    1: "empty",
    2: "optimized_circuit",
    4: "optimized_instruction_count",
    6: "default",
}

OPTIMIZATIONS = {
    1: "empty",
    2: "default_mapping_pass",
    4: "full_peephole_optimise",
    8: "context_simplify",
    18: "one",
    30: "two",
    32: "clifford_simplify",
    64: "decompose_controlled_gates",
    128: "globalise_phased_x",
    256: "kak_decomposition",
    512: "peephole_optimise_2q",
    1024: "remove_discarded",
    2048: "remove_barriers",
    4096: "remove_redundancies",
    8192: "three_qubit_squash",
    16384: "simplify_measured",
}


class OQCJob(QuantumJob):
    """Oxford Quantum Circuit job class."""

    def __init__(self, job_id: str, qpu_id: str, client: OQCClient, **kwargs):
        super().__init__(job_id=job_id, **kwargs)
        self._qpu_id = qpu_id
        self._client = client

    def cancel(self) -> None:
        """Cancel the task."""
        self._client.cancel_task(task_id=self.id, qpu_id=self._qpu_id)

    def result(self, **kwargs) -> OQCJobResult:
        """Get the result of the task."""
        self.wait_for_final_state()
        status = self.status(**kwargs)
        timings = self.get_timings()
        success = status == JobStatus.COMPLETED

        result_data = {
            "timings": timings,
            "success": success,
            "error_details": None,
            "counts": None,
        }

        if success:
            qpu_task_result = self._client.get_task_results(
                task_id=self.id, qpu_id=self._qpu_id, **kwargs
            )

            if not qpu_task_result:
                raise ResourceNotFoundError("No result found for the task")

            result_data["counts"] = qpu_task_result.result.get("c")

        else:
            result_data["error_details"] = self.get_errors(**kwargs)

        return OQCJobResult(result_data)

    def status(self, **kwargs) -> JobStatus:
        """Get the status of the task."""
        task_status = self._client.get_task_status(task_id=self.id, qpu_id=self._qpu_id, **kwargs)

        status_map = {
            "CREATED": JobStatus.INITIALIZING,
            "SUBMITTED": JobStatus.INITIALIZING,
            "RUNNING": JobStatus.RUNNING,
            "FAILED": JobStatus.FAILED,
            "CANCELLED": JobStatus.CANCELLED,
            "COMPLETED": JobStatus.COMPLETED,
            "UNKNOWN": JobStatus.UNKNOWN,
            "EXPIRED": JobStatus.FAILED,
        }

        return status_map.get(task_status, JobStatus.UNKNOWN)

    def metadata(self, use_cache: bool = False) -> dict[str, Any]:
        """Get the metadata for the task."""
        if not use_cache:
            status = self.status()
            self._cache_metadata["status"] = status
            provider_metadata = self._client.get_task_metadata(task_id=self.id, qpu_id=self._qpu_id)
            del provider_metadata["id"]

            config = json.loads(provider_metadata["config"])
            del config["$type"]

            provider_metadata["shots"] = config["$data"]["repeats"]
            provider_metadata["repetition_period"] = config["$data"]["repetition_period"]
            provider_metadata["results_format"] = RESULTS_FORMAT[
                config["$data"]["results_format"]["$data"]["transforms"]["$value"]
            ]
            provider_metadata["metrics"] = METRICS[config["$data"]["metrics"]["$value"]]
            provider_metadata["active_calibrations"] = config["$data"]["active_calibrations"]
            try:
                provider_metadata["optimizations"] = OPTIMIZATIONS[
                    config["$data"]["optimizations"]["$data"]["tket_optimizations"]["$value"]
                ]
            except TypeError:
                provider_metadata["optimizations"] = None
            provider_metadata["error_mitigation"] = config["$data"]["error_mitigation"]

            del provider_metadata["config"]
            self._cache_metadata.update(provider_metadata)
        return self._cache_metadata

    def metrics(self, **kwargs) -> dict[str, Any]:
        """Get the metrics for the task."""
        return self._client.get_task_metrics(task_id=self.id, qpu_id=self._qpu_id, **kwargs)

    def get_timings(self, **kwargs) -> dict[str, Any]:
        """Get the timings for the task."""
        return self._client.get_task_timings(task_id=self.id, qpu_id=self._qpu_id, **kwargs)

    def get_errors(self, **kwargs) -> Optional[QPUTaskErrors]:
        """Get the error message for the task."""
        if self.status(**kwargs) != JobStatus.FAILED:
            return None

        try:
            return self._client.get_task_errors(
                task_id=self.id, qpu_id=self._qpu_id, **kwargs
            ).error_message
        except AttributeError:
            return None

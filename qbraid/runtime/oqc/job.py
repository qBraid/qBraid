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
from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import GateModelResultData, Result

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

    def __init__(self, job_id: str, client: OQCClient, **kwargs):
        super().__init__(job_id=job_id, **kwargs)
        self._client = client
        self._qpu_id: Optional[str] = None
        self._terminal_status: Optional[JobStatus] = None

    @property
    def qpu_id(self) -> str:
        """Return the QPU ID."""
        if self._qpu_id is not None:
            return self._qpu_id

        if self._device is not None:
            self._qpu_id = self._device.id
        else:
            task_metadata = self._client.get_task_metadata(task_id=self.id)
            self._qpu_id = task_metadata["qpu_id"]

        return self._qpu_id

    def status(self) -> JobStatus:
        """Get the status of the task."""
        if self._terminal_status is not None:
            return self._terminal_status

        task_status = self._client.get_task_status(task_id=self.id, qpu_id=self.qpu_id)

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

        status = status_map.get(task_status, JobStatus.UNKNOWN)

        if status in JobStatus.terminal_states():
            if status == JobStatus.FAILED:
                errors = self.get_errors() or {}
                error_message = errors.get("message")

                if error_message is not None:
                    status.set_status_message(error_message)

            self._terminal_status = status

        return status

    def cancel(self) -> None:
        """Cancel the task."""
        self._client.cancel_task(task_id=self.id, qpu_id=self.qpu_id)

    @staticmethod
    def _get_counts(
        result: dict[str, dict[str, int]]
    ) -> Union[dict[str, int], list[dict[str, int]]]:
        """Extracts the measurement counts from the result of a quantum task.

        Args:
            result (dict[str, dict[str, int]]): A dictionary QPU task result,
                expected to contain one or more keys (the measurement registers),
                with values being dictionaries of bitstring counts.

        Returns:
            dict[str, int] or list[dict[str, int]]: If the result contains exactly one key,
                it returns the corresponding dictionary of measurement counts.
                If the result contains more than one key, it returns a list of dictionaries.

        Raises:
            ValueError: If the result dictionary is empty.

        Example:

        .. code-block:: python

            >>> result = {'c': {'00': 1000, '01': 500}}
            >>> OQCJob._get_counts(result)
            {'00': 1000, '01': 500}

            >>> result = {
            ...     'c0': {'000000': 45, '111111': 55},
            ...     'c1': {'000000': 45, '111111': 55}
            ... }
            >>> OQCJob._get_counts(result)
            [{'000000': 45, '111111': 55}, {'000000': 45, '111111': 55}]
        """
        if not result:
            raise ValueError("The result dictionary must not be empty.")

        if len(result) == 1:
            return next(iter(result.values()))
        return list(result.values())

    def result(self) -> Result:
        """Get the result of the task."""
        self.wait_for_final_state()

        task_data = self.metadata()
        task_data.update(
            {"errors": self.get_errors(), "metrics": self.metrics(), "timings": self.get_timings()}
        )

        job_id = task_data.pop("job_id", self.id)

        if self.status() != JobStatus.COMPLETED:
            data = GateModelResultData(measurement_counts=None)
            return Result(
                device_id=self.qpu_id, job_id=job_id, success=False, data=data, **task_data
            )

        task_results = self._client.get_task_results(task_id=self.id, qpu_id=self.qpu_id)
        if not task_results or not task_results.result:
            raise ResourceNotFoundError("No result found for the task")

        counts = self._get_counts(task_results.result)
        data = GateModelResultData(measurement_counts=counts)
        return Result(device_id=self.qpu_id, job_id=job_id, success=True, data=data, **task_data)

    def metadata(self) -> dict[str, Any]:
        """Get the metadata for the task."""
        status = self.status()
        self._cache_metadata["status"] = status
        provider_metadata = self._client.get_task_metadata(task_id=self.id, qpu_id=self.qpu_id)
        del provider_metadata["id"]

        config = json.loads(provider_metadata["config"])
        del config["$type"]

        config_data: dict[str, Any] = config["$data"]
        provider_metadata["shots"] = config_data["repeats"]
        provider_metadata["repetition_period"] = config_data["repetition_period"]
        provider_metadata["results_format"] = RESULTS_FORMAT[
            config_data["results_format"]["$data"]["transforms"]["$value"]
        ]
        provider_metadata["metrics"] = METRICS[config_data["metrics"]["$value"]]
        provider_metadata["active_calibrations"] = config["$data"]["active_calibrations"]
        try:
            provider_metadata["optimizations"] = OPTIMIZATIONS[
                config_data["optimizations"]["$data"]["tket_optimizations"]["$value"]
            ]
        except TypeError:
            provider_metadata["optimizations"] = None
        provider_metadata["error_mitigation"] = config_data.get("error_mitigation")

        del provider_metadata["config"]
        self._cache_metadata.update(provider_metadata)
        return self._cache_metadata

    def metrics(self) -> dict[str, Any]:
        """Get the metrics for the task."""
        return self._client.get_task_metrics(task_id=self.id, qpu_id=self.qpu_id)

    def get_timings(self) -> dict[str, Any]:
        """Get the timings for the task."""
        return self._client.get_task_timings(task_id=self.id, qpu_id=self.qpu_id)

    def get_errors(self) -> Optional[dict[str, Any]]:
        """Get the error message for the task."""
        task_errors = self._client.get_task_errors(task_id=self.id, qpu_id=self.qpu_id)
        if task_errors is None:
            return None

        return {
            "message": getattr(task_errors, "error_message", None),
            "code": getattr(task_errors, "error_code", None),
        }

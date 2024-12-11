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
Device class for OQC devices.

"""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional, Union

import pyqasm
from qcaas_client.client import QPUTask
from qcaas_client.compiler_config import (
    CompilerConfig,
    MetricsType,
    QuantumResultsFormat,
    Tket,
    TketOptimizations,
)

from qbraid._logging import logger
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import ResourceNotFoundError

from .job import OQCJob

if TYPE_CHECKING:
    import qcaas_client.client

    import qbraid.runtime

RESULTS_FORMAT = {
    "binary": QuantumResultsFormat().binary_count(),
    "raw": QuantumResultsFormat().raw(),
}

METRICS_TYPE = {
    "default": MetricsType.Default,
    "empty": MetricsType.Empty,
    "optimized_circuit": MetricsType.OptimizedCircuit,
    "optimized_instruction_count": MetricsType.OptimizedInstructionCount,
}

OPTIMIZATIONS = {
    "clifford_simplify": Tket(TketOptimizations.CliffordSimp),
    "context_simplify": Tket(TketOptimizations.ContextSimp),
    "decompose_controlled_gates": Tket(TketOptimizations.DecomposeArbitrarilyControlledGates),
    "default_mapping_pass": Tket(TketOptimizations.DefaultMappingPass),
    "empty": Tket(TketOptimizations.Empty),
    "full_peephole_optimise": Tket(TketOptimizations.FullPeepholeOptimise),
    "globalise_phased_x": Tket(TketOptimizations.GlobalisePhasedX),
    "kak_decomposition": Tket(TketOptimizations.KAKDecomposition),
    "one": Tket(TketOptimizations.One),
    "peephole_optimise_2q": Tket(TketOptimizations.PeepholeOptimise2Q),
    "remove_barriers": Tket(TketOptimizations.RemoveBarriers),
    "remove_discarded": Tket(TketOptimizations.RemoveDiscarded),
    "remove_redundancies": Tket(TketOptimizations.RemoveRedundancies),
    "simplify_measured": Tket(TketOptimizations.SimplifyMeasured),
    "three_qubit_squash": Tket(TketOptimizations.ThreeQubitSquash),
    "two": Tket(TketOptimizations.Two),
}


class OQCDevice(QuantumDevice):
    """Device class for OQC devices."""

    def __init__(
        self, profile: qbraid.runtime.TargetProfile, client: qcaas_client.client.OQCClient
    ):
        super().__init__(profile=profile)
        self._client = client

    @property
    def client(self) -> qcaas_client.client.OQCClient:
        """Returns the client for the device."""
        return self._client

    def __str__(self):
        """String representation of the OQCDevice object."""
        return f"{self.__class__.__name__}('{self.profile.device_name}')"

    def queue_depth(self) -> int:
        """Returns the number of tasks in the queue for the device."""
        try:
            exec_estimates = self._client.get_qpu_execution_estimates(qpu_ids=self.id)
            return exec_estimates["qpu_wait_times"][0]["tasks_in_queue"]
        except Exception as err:  # pylint: disable=broad-exception-caught
            raise ResourceNotFoundError("Queue depth is not available for this device.") from err

    def status(self) -> DeviceStatus:
        """Returns the status of the device."""
        feature_set: dict = self.profile.get("feature_set", {})
        always_on: bool = feature_set.get("always_on", False)
        if always_on:
            return DeviceStatus.ONLINE

        devices = self._client.get_qpus()
        device: Optional[dict] = next((d for d in devices if d["id"] == self.id), None)
        if not device:
            raise ResourceNotFoundError(f"Device '{self.id}' not found.")

        status: str = device.get("status", "")

        if status and status.upper() == "INACTIVE":
            return DeviceStatus.OFFLINE

        try:
            start_time = self.get_next_window()
            now = datetime.datetime.now()

            if now > start_time:  # TODO: does this comparison correctly account for timezones?
                return DeviceStatus.ONLINE
        except ResourceNotFoundError as err:  # pylint: disable=broad-exception-caught
            logger.info(err)

        return DeviceStatus.UNAVAILABLE

    def get_next_window(self) -> datetime.datetime:
        """
        Returns the start time of the next active window for the device.

        Note: Currently only AWS windows are defined.
        """
        try:
            start_time = self._client.get_next_window(self.id)
        except Exception as next_window_err:  # pylint: disable=broad-exception-caught
            try:
                exec_estimates = self._client.get_qpu_execution_estimates(qpu_ids=self.id)
                start_time = exec_estimates["qpu_wait_times"][0]["windows"][0]["start_time"]
            except Exception as exec_est_error:  # pylint: disable=broad-exception-caught
                logger.error(exec_est_error)
                raise ResourceNotFoundError(
                    f"Falied to fetch next active window for device '{self.id}'. "
                    "Note: Currently only AWS windows are defined."
                ) from next_window_err

        return datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

    def transform(self, run_input: str) -> str:
        """Transforms the input program before submitting it to the device."""
        qasm_module = pyqasm.loads(run_input)
        qasm_module.remove_includes()
        qasm_no_includes = pyqasm.dumps(qasm_module)
        return qasm_no_includes

    @staticmethod
    def _build_compiler_config(**kwargs) -> CompilerConfig:
        """Builds a compiler configuration object from the provided kwargs."""
        configs = {
            "shots",
            "repeats",
            "repetition_period",
            "results_format",
            "metrics",
            "active_calibrations",
            "optimizations",
            "error_mitigation",
        }

        unsupported_keys = set(kwargs) - configs
        if unsupported_keys:
            raise ValueError(f"Unsupported keyword arguments: {', '.join(unsupported_keys)}")

        default_values = {
            "shots": None,
            "repeats": None,
            "repetition_period": None,
            "results_format": "binary",
            "metrics": "default",
            "active_calibrations": None,
            "optimizations": None,
            "error_mitigation": None,
        }

        config_values = {key: kwargs.get(key, default) for key, default in default_values.items()}

        try:
            return CompilerConfig(
                repeats=config_values["shots"] or config_values["repeats"],
                repetition_period=config_values["repetition_period"],
                results_format=RESULTS_FORMAT[config_values["results_format"]],
                metrics=METRICS_TYPE[config_values["metrics"]],
                active_calibrations=config_values["active_calibrations"],
                optimizations=(
                    OPTIMIZATIONS[config_values["optimizations"]]
                    if config_values["optimizations"]
                    else None
                ),
                error_mitigation=config_values["error_mitigation"],
            )
        except KeyError as err:
            raise ValueError(f"Invalid configuration option: {err.args[0]}") from err

    # pylint: disable-next=arguments-differ
    def submit(self, run_input, **kwargs) -> Union[OQCJob, list[OQCJob]]:
        """Submit one or more jobs to the device."""
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        config = self._build_compiler_config(**kwargs) if any(kwargs) else None
        tasks = [QPUTask(program=program, config=config, qpu_id=self.id) for program in run_input]
        qpu_tasks = self._client.schedule_tasks(tasks, qpu_id=self.id)
        jobs = [OQCJob(job_id=task.task_id, device=self, client=self._client) for task in qpu_tasks]
        return jobs[0] if is_single_input else jobs

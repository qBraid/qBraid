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
import json
from typing import TYPE_CHECKING, Any, Union

from qcaas_client.client import QPUTask
from qcaas_client.compiler_config import (
    CompilerConfig,
    MetricsType,
    QuantumResultsFormat,
    Tket,
    TketOptimizations,
)

from qbraid.passes.qasm.compat import rename_qasm_registers
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

    @staticmethod
    def _decode_feature_set(data: dict[str, Any]) -> dict[str, Any]:
        """Decode the device feature set data."""
        feature_set: Union[str, dict] = data.get("feature_set", {})

        if isinstance(feature_set, dict):
            return data

        try:
            feature_set_decoded = json.loads(feature_set)
        except json.JSONDecodeError as err:
            raise ValueError(
                f"Failed to decode feature set data for device '{data.get('id')}'."
            ) from err

        data["feature_set"] = feature_set_decoded

        return data

    def status(self) -> DeviceStatus:
        """Returns the status of the device."""
        devices: list[dict] = self._client.get_qpus()
        for device in devices:
            device = self._decode_feature_set(device)
            if device["id"] == self.id:
                if device["feature_set"]["always_on"]:
                    return DeviceStatus.ONLINE
                now = datetime.datetime.now()
                start_time = self._client.get_next_window()
                temp = start_time.split(" ")
                year, month, day = map(int, temp[0].split("-"))
                hour, minute, second = map(int, temp[1].split(":"))
                start_time = datetime.datetime(year, month, day, hour, minute, second)
                if now > start_time:
                    return DeviceStatus.ONLINE
                return DeviceStatus.OFFLINE
        raise ResourceNotFoundError(f"Device {self.id} not found")

    def transform(self, run_input: str) -> str:
        """Transforms the input program before submitting it to the device."""
        return rename_qasm_registers(run_input)

    # pylint: disable-next=arguments-differ
    def submit(self, run_input, **kwargs) -> Union[OQCJob, list[OQCJob]]:
        """Submit one or more jobs to the device."""
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        tasks = []

        configs = ["shots", "repetition_period", "results_format", "metrics", "optimizations"]

        if any(key in kwargs for key in configs):
            custom_config = CompilerConfig(
                repeats=kwargs.get("shots", 1000),
                repetition_period=kwargs.get("repetition_period", 200e-6),
                results_format=RESULTS_FORMAT[kwargs.get("results_format", "binary")],
                metrics=METRICS_TYPE[kwargs.get("metrics", "default")],
                optimizations=OPTIMIZATIONS[kwargs.get("optimizations", "one")],
            )
        else:
            custom_config = None

        for program in run_input:
            task = QPUTask(program=program, config=custom_config, qpu_id=self.id)
            tasks.append(task)

        qpu_tasks = self._client.schedule_tasks(tasks, qpu_id=self.id)
        jobs = [OQCJob(job_id=task.task_id, device=self, client=self._client) for task in qpu_tasks]
        return jobs[0] if is_single_input else jobs

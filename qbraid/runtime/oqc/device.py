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
from qcaas_client.client import QPUTask
from scc.compiler.config import (CompilerConfig, QuantumResultsFormat,
                                 Tket, TketOptimizations, MetricsType)

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus, DeviceType
from qbraid.transforms.qasm2.passes import rename_qasm_registers

from .job import OQCJob

results_format = {
    "binary": QuantumResultsFormat().binary_count(),
    "raw": QuantumResultsFormat().raw()
}

metrics_type = {
    "default": MetricsType.Default,
    "empty": MetricsType.Empty,
    "optimized_circuit": MetricsType.OptimizedCircuit,
    "optimized_instruction_count": MetricsType.OptimizedInstructionCount
}

optimizations = {
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
    "two": Tket(TketOptimizations.Two)
}

class OQCDevice(QuantumDevice):
    """Device class for OQC devices."""
    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        client: "qcaas_client.client.OQCClient"
    ):
        super().__init__(profile=profile)
        self._client = client

    @property
    def client(self) -> "qcaas_client.client.OQCClient":
        """Returns the client for the device."""
        return self._client

    def status(self) -> DeviceStatus:
        if self.profile.get("device_type") == DeviceType.SIMULATOR:
            return DeviceStatus.ONLINE
        raise NotImplementedError("Only OQC simulators are supported")

    def transform(self, run_input: str) -> str:
        run_input = rename_qasm_registers(run_input)
        return run_input

    def submit(self, run_input, *args, **kwargs) -> OQCJob:
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        tasks = []

        if ("shots" in kwargs or "repetition_period" in kwargs or "results_format" in kwargs
            or "metrics" in kwargs or "optimizations" in kwargs):
            custom_config = CompilerConfig(
                repeats = kwargs.get("shots", 1000),
                repetition_period = kwargs.get("repetition_period", 200e-6),
                results_format = results_format[kwargs.get("results_format", "binary")],
                metrics = metrics_type[kwargs.get("metrics", "default")],
                optimizations = optimizations[kwargs.get("optimizations",  "one")]
            )
        else:
            custom_config = None
        for program in run_input:
            task = QPUTask(program=program, config = custom_config)
            tasks.append(task)

        qpu_tasks = self._client.schedule_tasks(tasks, qpu_id = self.id)
        job_ids = [task.task_id for task in qpu_tasks]

        jobs = [OQCJob(job_id=id_str, qpu_id=self.id, client=self._client) for id_str in job_ids]

        return jobs if not is_single_input else OQCJob(job_id = job_ids[0],
                                                       qpu_id = self.id, client=self._client)
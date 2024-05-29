# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus, DeviceType
from qbraid.transforms.qasm2.passes import rename_qasm_registers

from qcaas_client.client import OQCClient, QPUTask
from scc.compiler.config import CompilerConfig, QuantumResultsFormat, Tket, TketOptimizations, MetricsType

from .job import OQCJob

results_format = {
    "binary": QuantumResultsFormat().binary_count(),
    "raw": QuantumResultsFormat().raw(),
    None: None
}

metrics_type = {
    "default": MetricsType.Default,
    "empty": MetricsType.Empty,
    "optimizedcircuit": MetricsType.OptimizedCircuit,
    "optimizedinstructioncount": MetricsType.OptimizedInstructionCount,
    None: None
}

optimizations = {
    "cliffordsimp": Tket(TketOptimizations.CliffordSimp),
    "contextsimp": Tket(TketOptimizations.ContextSimp),
    "decomposearbitrarilycontrolledgates": Tket(TketOptimizations.DecomposeArbitrarilyControlledGates),
    "defaultmappingpass": Tket(TketOptimizations.DefaultMappingPass),
    "empty": Tket(TketOptimizations.Empty),
    "fullpeepholeoptimise": Tket(TketOptimizations.FullPeepholeOptimise),
    "globalisephrasedx": Tket(TketOptimizations.GlobalisePhasedX),
    "kakdecomposition": Tket(TketOptimizations.KAKDecomposition),
    "one": Tket(TketOptimizations.One),
    "peepholeoptimise2q": Tket(TketOptimizations.PeepholeOptimise2Q),
    "removebarriers": Tket(TketOptimizations.RemoveBarriers),
    "removediscarded": Tket(TketOptimizations.RemoveDiscarded),
    "removeredundancies": Tket(TketOptimizations.RemoveRedundancies),
    "simplifymeasured": Tket(TketOptimizations.SimplifyMeasured),
    "threequbitsquash": Tket(TketOptimizations.ThreeQubitSquash),
    "two": Tket(TketOptimizations.Two),
    None: None
}

class OQCDevice(QuantumDevice):

    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        client: "qcaas_client.client.OQCClient"
    ):
        super().__init__(profile=profile)
        self._client = client

    @property
    def client(self) -> "qcaas_client.client.OQCClient":
        return self._client
    
    def status(self) -> DeviceStatus:
        if self.profile.get("device_type") == DeviceType.SIMULATOR:
            return DeviceStatus.ONLINE
        else:
            raise NotImplementedError("Only OQC simulators are supported")

    def transform(self, program: str) -> str:
        program = rename_qasm_registers(program)
        return program
    
    def submit(self, run_input, **kwargs) -> OQCJob:
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        tasks = []

        # grab repeats, repetition_period, results_format, metrics, and optimizations from kwargs
        if "shots" in kwargs or "repetition_period" in kwargs or "results_format" in kwargs or "metrics" in kwargs or "optimizations" in kwargs:
            custom_config = CompilerConfig(
                repeats = kwargs.get("shots", None),
                repetition_period = kwargs.get("repetition_period", None),
                results_format = results_format[kwargs.get("results_format", None)],
                metrics = metrics_type[kwargs.get("metrics", None)],
                optimizations = optimizations[kwargs.get("optimizations",  None)]
            )
        else:
            custom_config = None
        for program in run_input:
            task = QPUTask(program=program, config = custom_config)
            tasks.append(task)

        qpu_tasks = self._client.schedule_tasks(tasks, qpu_id = self.id)
        job_ids = [task.task_id for task in qpu_tasks]

        return [OQCJob(job_id = id_str, qpu_id = self.id, client=self._client) for id_str in job_ids] if not is_single_input else OQCJob(job_id = job_ids[0], qpu_id = self.id, client=self._client)



    

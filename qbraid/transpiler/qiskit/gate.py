from typing import Iterable, Union

from qiskit.circuit import Instruction, Parameter

from qbraid.transpiler.gate import GateWrapper

from .._utils import get_qiskit_gate_data


class QiskitGateWrapper(GateWrapper):
    def __init__(self, gate: Instruction, params: Union[int, Iterable[int]] = None):
        super().__init__()

        self.gate = gate
        self.params = params
        self.name = gate.name

        data = get_qiskit_gate_data(gate)

        self.matrix = data["matrix"]
        self.num_controls = data["num_controls"]

        self.gate_type = data["type"]

    def get_abstract_params(self):
        return [p for p in self.params if isinstance(p, Parameter)]

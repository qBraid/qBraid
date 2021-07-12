from typing import Union, Iterable

from qiskit.circuit import Instruction
from qiskit.circuit import Parameter

from .utils import get_qiskit_gate_data
from ..gate import GateWrapper


class QiskitGateWrapper(GateWrapper):
    def __init__(self, gate: Instruction, params: Union[int, Iterable[int]] = None):

        super().__init__()

        self.gate = gate
        self.params = params
        self.name = gate.name

        data = get_qiskit_gate_data(gate)

        self.matrix = data["matrix"]
        self.num_controls = data["num_controls"]

        self._gate_type = data["type"]
        self._outputs["qiskit"] = gate
        self._package = "qiskit"

    def get_abstract_params(self):
        return [p for p in self.params if isinstance(p, Parameter)]

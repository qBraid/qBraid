from typing import Union

from cirq import Gate
from cirq.ops.measurement_gate import MeasurementGate
from sympy import Symbol

from qbraid.transpiler.gate import GateWrapper

from .._utils import get_cirq_gate_data

CirqGate = Union[Gate, MeasurementGate]


class CirqGateWrapper(GateWrapper):
    def __init__(self, gate: CirqGate):

        super().__init__()

        self.gate = gate
        self.name = None

        data = get_cirq_gate_data(gate)

        self.matrix = data["matrix"]
        self.params = data["params"]
        self.num_controls = data["num_controls"]

        self.gate_type = data["type"]

    def get_abstract_params(self):
        if self.params is not None:
            return [p for p in self.params if isinstance(p, Symbol)]
        return []

    def parse_params(self, input_param_mapping):
        self.params = [input_param_mapping[p] if isinstance(p, Symbol) else p for p in self.params]

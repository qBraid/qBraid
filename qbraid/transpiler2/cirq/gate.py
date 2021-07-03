from ..gate import GateWrapper
from cirq import Gate
from cirq.ops.measurement_gate import MeasurementGate
from .utils import get_cirq_gate_data
from typing import Union
from sympy import Symbol as CirqParameter

CirqGate = Union[Gate, MeasurementGate]


class CirqGateWrapper(GateWrapper):
    def __init__(self, gate: CirqGate, params: list = []):

        super().__init__()

        self.gate = gate
        self.name = None
        self.params = params

        data = get_cirq_gate_data(gate)

        self.matrix = data["matrix"]

        self.num_controls = data["num_controls"]

        self._gate_type = data["type"]
        self._outputs["cirq"] = gate

    def get_abstract_params(self):
        if not (self.params == None):
            return [p for p in self.params if isinstance(p, CirqParameter)]
        else:
            return []

    @property
    def package(self):
        return "cirq"

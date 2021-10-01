"""CirqGateWrapper Class"""

from typing import Union

from cirq import Gate
from cirq.ops.measurement_gate import MeasurementGate
from sympy import Symbol

from qbraid.transpiler._utils import get_cirq_gate_data
from qbraid.transpiler.gate import GateWrapper

CirqGate = Union[Gate, MeasurementGate]


class CirqGateWrapper(GateWrapper):
    """Wrapper class for Cirq ``Gate`` objects."""

    def __init__(self, gate: CirqGate):
        """Create a CirqGateWrapper

        Args:
            gate: the cirq ``Gate`` to be wrapped.

        """
        super().__init__()

        self.gate = gate
        self.name = None

        data = get_cirq_gate_data(gate)

        self.matrix = data["matrix"]
        self.params = data["params"]
        self.num_controls = data["num_controls"]

        self.gate_type = data["type"]

    def get_abstract_params(self):
        """Return list of the circuit's params. If not paramterized, return empty list."""
        if self.params is not None:
            return [p for p in self.params if isinstance(p, Symbol)]
        return []

    def parse_params(self, input_param_mapping):
        """Adapt gate wrapper ``params`` attribute to specified input paramater mapping."""
        self.params = [input_param_mapping[p] if isinstance(p, Symbol) else p for p in self.params]

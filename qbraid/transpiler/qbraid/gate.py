"""QbraidGateWrapper Class"""

from qbraid.circuits.controlledgate import ControlledGate as QbraidControlledGate
from qbraid.circuits.gate import Gate as QbraidGate
from qbraid.circuits.parameter import Parameter as QbraidParameter

from qbraid.transpiler.gate import GateWrapper


class QbraidGateWrapper(GateWrapper):
    """Wrapper class for qBraid ``Gate`` objects."""

    def __init__(self, gate: QbraidGate):
        """Create a QbraidGateWrapper

        Args:
            gate: the qbraid ``Gate`` object to be wrapped

        """
        super().__init__()

        self.gate = gate
        self.name = gate.name
        self.gate_type = self.name
        self.params = gate.params
        self.num_controls = gate.num_ctrls if isinstance(gate, QbraidControlledGate) else 0

    def get_abstract_params(self):
        """Return list of the circuits parameters. Return empty list if not parameterized."""
        if self.params is not None:
            return [p for p in self.params if isinstance(p, QbraidParameter)]
        return []

    def parse_params(self, input_param_mapping):
        """Adapt the gate wrapper ``params`` attribute to the specified input parameter mapping."""
        self.params = [
            input_param_mapping[p] if isinstance(p, QbraidParameter) else p for p in self.params
        ]

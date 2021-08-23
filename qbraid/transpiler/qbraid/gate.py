from qbraid.circuits.controlledgate import \
    ControlledGate as QbraidControlledGate
from qbraid.circuits.gate import Gate as QbraidGate
from qbraid.circuits.parameter import Parameter as QbraidParameter

from ..gate import GateWrapper


class QbraidGateWrapper(GateWrapper):
    def __init__(self, gate: QbraidGate):
        super().__init__()

        self.gate = gate
        self.name = gate.name
        self.gate_type = self.name
        self.params = gate.params
        self.num_controls = gate.num_ctrls if isinstance(gate, QbraidControlledGate) else 0

    def get_abstract_params(self):
        if self.params is not None:
            return [p for p in self.params if isinstance(p, QbraidParameter)]
        return []

    def parse_params(self, input_param_mapping):
        self.params = [
            input_param_mapping[p] if isinstance(p, QbraidParameter) else p for p in self.params
        ]

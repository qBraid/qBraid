from ..gate import AbstractGate
from cirq import Gate as CirqGate
from .utils import get_cirq_gate_data


class CirqGateWrapper(AbstractGate):
    def __init__(self, gate: CirqGate):

        super().__init__()

        self.gate = gate
        self.name = None

        data = get_cirq_gate_data(gate)

        self.matrix = data["matrix"]
        self.params = data["params"]
        self.num_controls = data["num_controls"]

        self._gate_type = data["type"]
        self._outputs["cirq"] = gate
        self.package = "cirq"

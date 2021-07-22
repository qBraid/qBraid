from braket.circuits.gate import Gate

from .._utils import get_braket_gate_data
from qbraid.transpiler.gate import GateWrapper


class BraketGateWrapper(GateWrapper):
    def __init__(self, gate: Gate):
        super().__init__()

        self.gate = gate
        self.name = None

        data = get_braket_gate_data(gate)

        self.matrix = data["matrix"]
        self.params = data["params"]

        if "base_gate" in data:
            self.base_gate = BraketGateWrapper(data["base_gate"])
            # self.base_gate = data['base_gate']
            self.num_controls = data["num_controls"]

        self.gate_type = data["type"]

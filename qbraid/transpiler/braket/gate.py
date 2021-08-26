"""BraketGateWrapper Class"""

from braket.circuits.gate import Gate

from qbraid.transpiler.gate import GateWrapper
from qbraid.transpiler._utils import get_braket_gate_data


class BraketGateWrapper(GateWrapper):
    """Wrapper class for Amazon Braket ``Gate`` objects."""

    def __init__(self, gate: Gate):
        """Create a BraketDeviceWrapper

        Args:
            gate: the Braket gate to be wrapped

        """
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

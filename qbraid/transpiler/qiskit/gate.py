"""QiskitGateWrapper Class"""

from typing import Iterable, Union

from qiskit.circuit import Instruction, Parameter

from qbraid.transpiler._utils import get_qiskit_gate_data
from qbraid.transpiler.gate import GateWrapper


class QiskitGateWrapper(GateWrapper):
    """Wrapper class for Qiskit ``Gate`` objects"""

    def __init__(self, gate: Instruction, params: Union[int, Iterable[int]] = None):
        """Create a QiskitGateWrapper

        Args:
            gate: the qiskit ``Gate`` object to be wrapped
            params: the gate's paramaters, None if gate is not parameterized

        """
        super().__init__()

        self.gate = gate
        self.params = params
        self.name = gate.name

        data = get_qiskit_gate_data(gate)

        self.matrix = data["matrix"]
        self.num_controls = data["num_controls"]

        self.gate_type = data["type"]

    def get_abstract_params(self):
        """Return a list of the gate's parameters."""
        return [p for p in self.params if isinstance(p, Parameter)]

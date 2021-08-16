from ...gate import Gate
from typing import Optional


class DCX(Gate):
    """
    A 2-qubit double CNOT gate consisting of two CNOTs place
    back-to-back with alternating control qubits.
    Args:
        global_phase[Optional]: The global phase on the gate
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("DCX", num_qubits=2, params=[], global_phase=global_phase)

    @property
    def num_params(self):
        return 0

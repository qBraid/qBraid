from ...gate import Gate
from typing import Optional

class DCX(Gate):
    """
    Two qubit double CNOT gate, 
    which is two CNOTs with opposite control qubits next to each other.
    Args:
        global_phase[Optional]: The global phase on the gate
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("DCX", num_qubits=2, params=[], global_phase=global_phase)

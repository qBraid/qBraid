from ...gate import Gate
from typing import Optional

class DCX(Gate):
    """2 qubit double CNOT gate, two CNOTs with opposite control qubits next to each other

    Args:
        Gate (ABC): Extension of basic gate class
    """
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("DCX", num_qubits=2, params=[], global_phase=global_phase)

from ...powgate import PowGate
from typing import Optional

class HPow(PowGate):
    """A single qubit Hadamard Gate to a specified power

    Args:
        PowGate (Gate): Extension of Power Gate class
    """

    def __init__(self, exponent: float=1.0, global_phase: Optional[float]=0.0):
        super().__init__(
            "HPow", 
            num_qubits=1, 
            params=[], 
            global_phase=global_phase, 
            exponent=exponent)
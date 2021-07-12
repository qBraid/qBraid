from ...gate import Gate
from typing import Optional


class S(Gate):
    """Single qubit gate with rotation of pi/2 about z-axis

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("S", num_qubits=1, params=[], global_phase=global_phase)

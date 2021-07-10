from ...gate import Gate
from typing import Optional


class Sdg(Gate):
    """Single qubit gate with rotation of -pi/2 about the z-axis

    Args:
        Gate (ABC): Extends basic gate class
    """
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("Sdg", num_qubits=1, params=[], global_phase=global_phase)

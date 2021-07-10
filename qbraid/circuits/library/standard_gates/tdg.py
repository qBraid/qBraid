from ...gate import Gate
from typing import Optional


class Tdg(Gate):
    """Single qubit rotation of -pi/4 about the z-axis

    Args:
        Gate (ABC): Extends the basic gate class
    """
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("Tdg", num_qubits=1, params=[], global_phase=global_phase)

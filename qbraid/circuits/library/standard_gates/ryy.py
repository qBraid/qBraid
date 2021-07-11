from ...gate import Gate
from typing import Optional


class RYY(Gate):
    """2 qubit rotation gate for rotation about YY
    with theta parameter

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, theta: float, global_phase: Optional[float] = 0.0):
        super().__init__("RYY", num_qubits=2, params=[theta], global_phase=global_phase)

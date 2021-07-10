from ...gate import Gate
from typing import Optional


class SXdg(Gate):
    """Single qubit negative Square Root X gate

    Also, know as -pi/4 rotation about the x-axis

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("SXdg", num_qubits=1, params=[], global_phase=global_phase)

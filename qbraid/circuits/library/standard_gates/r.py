from ...gate import Gate
from typing import Optional


class R(Gate):
    """Single qubit rotation gate for any rotation around the x-y plane
    with theta and phi parameters

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, theta: float, phi: float, global_phase: Optional[float] = 0.0):
        super().__init__(
            "R", num_qubits=1, params=[theta, phi], global_phase=global_phase
        )

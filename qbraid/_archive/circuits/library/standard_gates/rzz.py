from typing import Optional

from ...gate import Gate


class RZZ(Gate):
    """2 qubit rotation gate about zz
    with phi parameter

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, phi: float, global_phase: Optional[float] = 0.0):
        super().__init__("RZZ", num_qubits=2, params=[phi], global_phase=global_phase)

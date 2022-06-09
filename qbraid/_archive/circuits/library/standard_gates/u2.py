from typing import Optional

from ...gate import Gate


class U2(Gate):
    """Single qubit rotation about the x+z axis
    with phi and lambda parameters

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, phi: float, lam: float, global_phase: Optional[float] = 0.0):
        super().__init__("U2", num_qubits=1, params=[phi, lam], global_phase=global_phase)

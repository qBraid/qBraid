from .powgate import PowGate
from typing import Optional


class XPow(PowGate):
    """Power Gate version of X gate with specified power

    Args:
        PowGate (Gate): Extends power gate class
    """

    def __init__(self, exponent: float = 1.0, global_phase: Optional[float] = 0.0):
        super().__init__(
            "XPow",
            num_qubits=1,
            params=[],
            global_phase=global_phase,
            exponent=exponent,
        )

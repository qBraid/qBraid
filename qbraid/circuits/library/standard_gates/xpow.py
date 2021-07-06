from ...powgate import PowGate
from typing import Optional


class XPow(PowGate):
    def __init__(self, exponent: float = 1.0, global_phase: Optional[float] = 0.0):
        super().__init__(
            "XPow", num_qubits=1, arams=[], global_phase=global_phase, exponent=exponent
        )

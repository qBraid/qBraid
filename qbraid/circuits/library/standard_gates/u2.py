from ...gate import Gate
from typing import Optional


class U2(Gate):
    def __init__(self, phi: float, lam: float, global_phase: Optional[float] = 0.0):
        super().__init__(
            "U2", num_qubits=1, params=[phi, lam], global_phase=global_phase
        )

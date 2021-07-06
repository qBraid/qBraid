from ...gate import Gate
from typing import Optional


class U3(Gate):
    def __init__(
        self, theta: float, phi: float, lam: float, global_phase: Optional[float] = 0.0
    ):
        super().__init__(
            "U3", num_qubits=1, params=[theta, phi, lam], global_phase=global_phase
        )

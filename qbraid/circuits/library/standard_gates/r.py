from ...gate import Gate
from typing import Optional


class R(Gate):
    def __init__(self, theta: float, phi: float, global_phase: Optional[float] = 0.0):
        super().__init__(
            "R", num_qubits=1, params=[theta, phi], global_phase=global_phase
        )

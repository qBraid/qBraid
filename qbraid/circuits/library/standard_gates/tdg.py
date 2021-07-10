from ...gate import Gate
from typing import Optional


class Tdg(Gate):
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("Tdg", num_qubits=1, params=[], global_phase=global_phase)

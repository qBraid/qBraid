from ...gate import Gate
from typing import Optional


class Measure(Gate):
    def __init__(self, global_phase: Optional[float]):
        super().__init__("measure", num_qubits=1, params=[], global_phase=global_phase)

from ...gate import Gate
from typing import Optional


class Measure(Gate):
    """Place single qubit measurement

    Args:
        Gate (ABC): Extends Basic gate class
    """
    def __init__(self, global_phase: Optional[float] = 0):
        super().__init__("measure", num_qubits=1, params=[], global_phase=global_phase)

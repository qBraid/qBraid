from ...gate import Gate
from typing import Optional


class I(Gate):
    """Single qubit identity gate that keeps qubit in same state

    Args:
        Gate (ABC): Extends basic gate class
    """
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("I", num_qubits=1, params=[], global_phase=global_phase)

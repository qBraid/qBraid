from ...gate import Gate
from typing import Optional


class pSwap(Gate):
    """2 qubit swap gate that will swap the phase of two qubits

    Args:
        Gate (ABC): Extends basic gate class
    """
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("pSwap", num_qubits=2, params=[], global_phase=global_phase)

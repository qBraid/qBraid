from typing import Optional

from ...gate import Gate


class I(Gate):
    """
    A single qubit identity gate that keeps qubit in same state
    for a wait cycle. Should not be optimized.
    Args:
        global_phase[Optional]: The global phase on the gate
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("I", num_qubits=1, params=[], global_phase=global_phase)

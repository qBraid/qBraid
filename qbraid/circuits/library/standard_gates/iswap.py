from typing import Optional

from ...gate import Gate


class iSwap(Gate):
    """
    A 2-qubit gate that will swap state and phase of two qubits.
    Args:
        global_phase[Optional]: The global phase on the gate
    """


class iSwap(Gate):
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("iSwap", num_qubits=2, params=[], global_phase=global_phase)

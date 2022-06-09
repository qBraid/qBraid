from typing import Optional

from ...gate import Gate


class Measure(Gate):
    """
    Place a single qubit measurement to collapse the state of the qubit.
    Args:
        global_phase[Optional]: The global phase on the gate
    """

    def __init__(self, global_phase: Optional[float] = 0):
        super().__init__("measure", num_qubits=1, params=[], global_phase=global_phase)

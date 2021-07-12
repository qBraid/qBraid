from ...powgate import PowGate
from typing import Optional


class HPow(PowGate):
    """
    A power version of the Hadamard gate.
    Args:
        exponent: Power to raise the gate to
        global_phase[Optional]: The global phase on the gate
    """

    def __init__(self, exponent: float = 1.0, global_phase: Optional[float] = 0.0):
        super().__init__(
            "HPow",
            num_qubits=1,
            params=[],
            global_phase=global_phase,
            exponent=exponent,
        )

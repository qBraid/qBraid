from ...gate import Gate
from ...controlledgate import ControlledGate
from typing import Optional


class RX(Gate):
    """Single qubit x rotation gate for any rotation around the x-axis
    with theta parameter

    Args:
        Gate (ABC): Extends basic gate class
    """
    def __init__(self, theta: float, global_phase: Optional[float] = 0.0):
        super().__init__("RX", num_qubits=1, params=[theta], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CRX(self._params[0], self._global_phase)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CRX(ControlledGate):
    """Controlled version of RX gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """
    def __init__(self, theta: float, global_phase: Optional[float] = 0.0):
        super().__init__(RX(theta), global_phase=global_phase)

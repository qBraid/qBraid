from typing import Optional

from ...controlledgate import ControlledGate
from ...gate import Gate


class Y(Gate):
    """Single qubit Y gate

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("Y", num_qubits=1, params=[], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CY(self._global_phase)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CY(ControlledGate):
    """Controlled version of Y gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__(Y(), global_phase=global_phase)

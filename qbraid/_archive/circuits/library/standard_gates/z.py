from typing import Optional

from ...controlledgate import ControlledGate
from ...gate import Gate


class Z(Gate):
    """Single qubit Z gate or phase flip gate

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("Z", num_qubits=1, params=[], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CZ(self._global_phase)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CZ(ControlledGate):
    """Controlled version of Z gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """

    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__(Z(), global_phase=global_phase)

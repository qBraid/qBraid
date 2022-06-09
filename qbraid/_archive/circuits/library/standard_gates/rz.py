from typing import Optional

from ...controlledgate import ControlledGate
from ...gate import Gate


class RZ(Gate):
    """Single qubit rotation gate for rotation around z-zxis
    with phi parameter

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, phi: float, global_phase: Optional[float] = 0.0):
        super().__init__("RZ", num_qubits=1, params=[phi], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CRZ(self._params[0], self._global_phase)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CRZ(ControlledGate):
    """Controlled version of RX gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """

    def __init__(self, phi: float, global_phase: Optional[float] = 0.0):
        super().__init__(RZ(phi), global_phase=global_phase)

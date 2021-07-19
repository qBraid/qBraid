from ...gate import Gate
from ...controlledgate import ControlledGate
from typing import Optional


class Phase(Gate):
    """Single qubit rotation about the x-y plane.
    Args:
        theta: Rotation in the x-y plane
        global_phase[Optional]: The global phase on the gate
    """

    def __init__(self, theta: float, global_phase: Optional[float] = 0.0):
        super().__init__(
            "Phase", num_qubits=1, params=[theta], global_phase=global_phase
        )

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CPhase(self._params[0], self._global_phase)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CPhase(ControlledGate):
    """Controlled version of phase gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """

    def __init__(self, theta: float, global_phase: Optional[float] = 0.0):
        super().__init__(Phase(theta), num_ctrls=1, global_phase=global_phase)

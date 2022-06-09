from typing import Optional

from ...controlledgate import ControlledGate
from ...gate import Gate


class U1(Gate):
    """Single qubit diagonal gate for rotations about the z-axis
    with theta parameter

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, theta: float, global_phase: Optional[float] = 0.0):
        super().__init__("U1", num_qubits=1, params=[theta], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CU1(self._params[0], self._global_phase)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CU1(ControlledGate):
    """Controlled version of U1 gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """

    def __init__(self, theta: float, global_phase: Optional[float] = 0.0):
        super().__init__(
            "CU1",
            num_qubits=2,
            params=[theta],
            global_phase=global_phase,
            num_ctrls=1,
            base_gate=U1,
        )

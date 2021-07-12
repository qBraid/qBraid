from ...gate import Gate
from ...controlledgate import ControlledGate
from typing import Optional


class U(Gate):
    """Single qubit generic rotation gate
    with theta, phi, and lambda parameters

    Args:
        Gate (ABC): Extends basic gate class
    """

    def __init__(self, theta: float, phi: float, lam: float, global_phase: Optional[float] = 0.0):
        super().__init__("U", num_qubits=1, params=[theta, phi, lam], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CU(
                self._params[0],
                self._params[1],
                self._params[2],
                global_phase=self._global_phase,
            )
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CU(ControlledGate):
    """Controlled version of U gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """

    def __init__(self, theta: float, phi: float, lam: float, global_phase: Optional[float] = 0.0):
        super().__init__(U(theta, phi, lam, global_phase=global_phase))

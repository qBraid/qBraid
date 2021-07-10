from ...gate import Gate
from ...controlledgate import ControlledGate
from typing import Optional


class SX(Gate):
    """Single qubit Square Root X gate, or x gate to 1/2 power

    Also, know as a rotation of pi/4 about the x-axis

    Args:
        Gate (ABC): Extends basic gate class
    """
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("SX", num_qubits=1, params=[], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CSX(base_gate = self)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CSX(ControlledGate):
    """Controlled version of SX gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """
    def __init__(self, base_gate = None, global_phase: Optional[float] = 0.0):
        if not base_gate:
            base_gate = SX()
        super().__init__(SX(),global_phase=global_phase)

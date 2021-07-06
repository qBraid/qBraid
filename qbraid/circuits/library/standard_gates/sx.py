from ...gate import Gate
from ...controlledgate import ControlledGate
from typing import Optional


class SX(Gate):
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("SX", num_qubits=1, params=[], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CSX(self._global_phase)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CSX(ControlledGate):
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__(
            "CSX",
            num_qubits=2,
            params=[],
            global_phase=global_phase,
            num_ctrls=1,
            base_gate=SX,
        )

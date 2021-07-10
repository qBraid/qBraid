from ...gate import Gate
from ...controlledgate import ControlledGate
from typing import Optional


class RZ(Gate):
    def __init__(self, phi: float, global_phase: Optional[float] = 0.0):
        super().__init__("RZ", num_qubits=1, params=[phi], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CRZ(self._params[0], self._global_phase)
        else:
            from ...controlledgate import ControlledGate

            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CRZ(ControlledGate):
    def __init__(self, phi: float, global_phase: Optional[float] = 0.0):
        super().__init__(RZ(phi), global_phase=global_phase)
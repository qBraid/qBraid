from ...gate import Gate
from ...controlledgate import ControlledGate
from typing import Optional


class H(Gate):
    """Single qubit hadamard Gate or superposition gate

    Args:
        Gate (ABC): Extension of basic gate class
    """
    def __init__(self, global_phase: Optional[float]=0.0):
        super().__init__(
            "H", 
            num_qubits=1, 
            params=[], 
            global_phase=global_phase)
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("H", num_qubits=1, params=[], global_phase=global_phase)

    def control(self, num_ctrls: int = 1):
        if num_ctrls == 1:
            return CH(self._global_phase)
        else:
            from ...controlledgate import ControlledGate
            
            return ControlledGate(base_gate=self, num_ctrls=num_ctrls)


class CH(ControlledGate):
    """Controlled version of Hadamard Gate

    Args:
        ControlledGate (Gate): Extends controlled gate class
    """
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__(H(),1, global_phase = global_phase,)

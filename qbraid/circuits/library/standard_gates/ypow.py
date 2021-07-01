from ...powgate import PowGate
from typing import Optional

class YPow(PowGate):

    def __init__(self, exponent: float=1.0, global_phase: Optional[float]=0.0):
        super().__init__(
            "YPow", 
            num_qubits=1, 
            params=[], 
            global_phase=global_phase, 
            exponent=exponent)
from ...gate import Gate
from typing import Optional

class RZZ(Gate):

    def __init__(self, phi: float, global_phase: Optional[float]=0.0):
        super().__init__(
            "RZZ", 
            num_qubits=2, 
            params=[phi], 
            global_phase=global_phase)
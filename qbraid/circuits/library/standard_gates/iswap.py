from ...gate import Gate
from typing import Optional

<<<<<<< HEAD
class iSwap(Gate):
    """2 qubit iSwap gate that will swap state and phase of two qubits

    Args:
        Gate (ABC): Extension of basic gate class
    """
=======
>>>>>>> 04ec590e17fa8a808f29650c735404918a2c4b99

class iSwap(Gate):
    def __init__(self, global_phase: Optional[float] = 0.0):
        super().__init__("iSwap", num_qubits=2, params=[], global_phase=global_phase)

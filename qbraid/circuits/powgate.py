from typing import Optional, List
from .gate import Gate

class PowGate(Gate):
    """Extension of gate for gates with a variable power.

    Args:
        Gate (Gate(ABC)): Extends basic gate class
    """

    def __init__(self, name: str, num_qubits: int, params: List, global_phase: Optional[float],
    exponent: float=1.0):
        super().__init__(name, num_qubits, params=params, global_phase=global_phase)
        self._exponent=exponent

    @property
    def exponent(self):
        return self._exponent

    @exponent.setter
    def exponent(self, power):
        self._exponent=power
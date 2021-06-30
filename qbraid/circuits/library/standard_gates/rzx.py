from ...gate import Gate
from typing import Optional

class RZX(Gate):

    def __init__(self, theta: float, exponent: Optional[float]=1.0):
        super().__init__("RXZ", 2, [theta], 0.0, exponent=exponent)

    @property
    def name(self):
        return self._name

    @property
    def num_qubits(self):
        return self._num_qubits

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, theta):
        self._params=[theta]

    @property
    def global_phase(self):
        return self._global_phase

    @property
    def exponent(self):
        return self._exponent

    @exponent.setter
    def exponent(self, exp):
        self._exponent=exp
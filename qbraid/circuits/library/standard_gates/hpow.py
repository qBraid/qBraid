from ...gate import Gate
from typing import Optional

class HPow(Gate):

    def __init__(self, exponent: Optional[float]=1.0):
        super().__init__("HPow", 1, [], 0.0, exponent=exponent)

    @property
    def name(self):
        return self._name

    @property
    def num_qubits(self):
        return self._num_qubits

    @property
    def params(self):
        return self._params

    @property
    def global_phase(self):
        return self._global_phase

    @property
    def exponent(self):
        return self._exponent

    @exponent.setter
    def exponent(self, exp):
        self._exponent=exp
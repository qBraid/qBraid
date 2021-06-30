from ...gate import Gate
from typing import Optional

class RZZ(Gate):

    def __init__(self, phi: float, exponent: Optional[float]=1.0):
        super().__init__("RZZ", 2, [phi], 0.0, exponent=exponent)

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
    def params(self, phi):
        self._params=[phi]

    @property
    def global_phase(self):
        return self._global_phase

    @property
    def exponent(self):
        return self._exponent

    @exponent.setter
    def exponent(self, exp):
        self._exponent=exp
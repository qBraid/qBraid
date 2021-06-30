from ...gate import Gate, ControlledGate
from typing import Optional

class RZ(Gate):

    def __init__(self, phi: float, exponent: Optional[float]=1.0):
        super().__init__("RZ", 1, [phi], -0.5, exponent=exponent)

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
        

class CRZ(ControlledGate):
    def __init__(self, phi, exponent: Optional[float]=1.0):
        super().__init__("CRZ", 2, [phi], 0.0, exponent=exponent, num_ctrls=1, base_gate=RZ)

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

    @property
    def num_ctrls(self):
        return self._num_ctrls

    @property
    def base_gate(self):
        return self._base_gate
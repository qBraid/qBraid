from ...gate import Gate, ControlledGate
from typing import Optional

class Phase(Gate):

    def __init__(self, theta: float, exponent: Optional[float]=1.0):
        super().__init__("Phase", 1, [theta], 0.0, exponent=exponent)

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


class CPhase(ControlledGate):

    def __init__(self, theta, exponent: Optional[float]=1.0):
        super().__init__("CPhase", 2, [theta], 0.0, exponent=exponent, num_ctrls=1, base_gate=Phase)

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

    @property
    def num_ctrls(self):
        return self._num_ctrls

    @property
    def base_gate(self):
        return self._base_gate
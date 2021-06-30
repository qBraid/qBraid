from ...gate import ControlledGate, Gate

class Z(Gate):

    def __init__(self):
        super().__init__("Z", 1, [], 0.0, 1.0)

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

class CZ(ControlledGate):

    def __init__(self):
        super().__init__("CZ", 2, [], 0.0, 1.0, num_ctrls=1, base_gate=Z)

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

    @property
    def num_ctrls(self):
        return self._num_ctrls

    @property
    def base_gate(self):
        return self._base_gate
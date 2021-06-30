from ...gate import Gate, ControlledGate

class SX(Gate):

    def __init__(self):
        super().__init__("SX", 1, [], 0.0, 0.5)

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


class CSX(ControlledGate):

    def __init__(self):
        super().__init__("CSX", 2, [], 0.0, 1.0, num_ctrls=1, base_gate=SX)

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
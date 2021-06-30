from ...gate import Gate

class SXdg(Gate):

    def __init__(self):
        super().__init__("SXdg", 1, [], 0.0, -0.5)

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
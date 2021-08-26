from qbraid.circuits.circuit import Circuit

from ..circuit import CircuitWrapper
from ..parameter import ParamID
from .moment import QbraidMomentWrapper


class QbraidCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: Circuit, input_qubit_mapping=None, input_param_mapping=None):

        super().__init__(circuit, input_qubit_mapping)

        self._package = "qbraid"

        self._qubits = list(range(circuit.num_qubits))
        self._params = circuit.params

        if not input_param_mapping:
            self._input_param_mapping = {
                p: ParamID(i, p.name) for i, p in enumerate(circuit.params)
            }

        self._params = self._input_param_mapping.values()

        self._wrap_circuit()

    def _wrap_circuit(self):

        self._moments = []

        for moment in self._circuit.moments:

            next_moment = QbraidMomentWrapper(moment)
            self._moments.append(next_moment)

            for instruction in next_moment.instructions:
                instruction.gate.parse_params(self.input_param_mapping)

    @property
    def instructions(self):
        instructions = []
        for m in self.moments:
            instructions += m.instructions
        return instructions

    @property
    def moments(self):
        return self._moments

    @property
    def num_qubits(self):
        return len(self.qubits)

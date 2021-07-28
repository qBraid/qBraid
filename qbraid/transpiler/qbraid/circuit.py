from ..circuit import CircuitWrapper
from .moment import QbraidMomentWrapper
from ..parameter import ParamID

from qbraid.circuits.circuit import Circuit

class QbraidCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: Circuit, input_qubit_mapping=None, input_param_mapping = None):

        super().__init__()

        self.circuit = circuit
        self._package = 'qbraid'

        self.qubits = list(range(circuit.num_qubits))
        #self.params = circuit.params #not implemented in circuit yet

        if not input_param_mapping:
            self.input_param_mapping = {p:ParamID(i,p.name) for i,p in enumerate(self.params)}

        for moment in circuit.moments:
            
            next_moment = QbraidMomentWrapper(moment)
            self.moments.append(next_moment)
            
            for instruction in next_moment.instructions:
                instruction.gate.parse_params(self.input_param_mapping)

    @property
    def num_qubits(self):
        return len(self.qubits)

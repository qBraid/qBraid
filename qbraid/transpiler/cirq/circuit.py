from cirq.circuits import Circuit

from qbraid.transpiler.circuit import CircuitWrapper
from .instruction import CirqInstructionWrapper


class CirqCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: Circuit, input_qubit_mapping=None):

        super().__init__()

        self.circuit = circuit
        self.qubits = circuit.all_qubits()
        self.input_qubit_mapping = (
            {qubit: index for index, qubit in enumerate(self.qubits)}
            if input_qubit_mapping is None
            else input_qubit_mapping
        )

        self.params = set()

        for op in circuit.all_operations():

            qbs = [self.input_qubit_mapping[qubit] for qubit in op.qubits]
            next_instruction = CirqInstructionWrapper(op, qbs)
            self.params.union(set(next_instruction.gate.get_abstract_params()))
            self.instructions.append(next_instruction)

        self.input_param_mapping = {param: index for index, param in enumerate(self.params)}

        for instruction in self.instructions:
            instruction.gate.parse_params(self.input_param_mapping)

        self._package = "cirq"

    @property
    def num_qubits(self):
        return len(self.qubits)


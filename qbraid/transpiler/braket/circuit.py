from braket.circuits.circuit import Circuit

from .instruction import BraketInstructionWrapper
from ..circuit import CircuitWrapper


class BraketCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: Circuit, input_qubit_mapping=None):

        super().__init__()

        self.circuit = circuit
        self.qubits = circuit.qubits
        self.input_qubit_mapping = (
            input_qubit_mapping
            if input_qubit_mapping
            else {q: i for i, q in enumerate(self.qubits)}
        )
        self.instructions = []

        for instruction in circuit.instructions:

            qubits = [self.input_qubit_mapping[q] for q in instruction.target]
            next_instruction = BraketInstructionWrapper(instruction, qubits)
            self.instructions.append(next_instruction)

    @property
    def num_qubits(self):
        return len(self.qubits)

    @property
    def package(self):
        return "braket"

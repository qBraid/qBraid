from ..circuit import CircuitWrapper
from .instruction import BraketInstructionWrapper
from qbraid.exceptions import PackageError
from braket.circuits.circuit import Circuit


class BraketCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: Circuit):

        super().__init__()

        self.circuit = circuit
        self.qubits = circuit.qubits
        self.input_mapping = {q: i for i, q in enumerate(self.qubits)}
        self.instructions = []

        for instruction in circuit.instructions:

            qubits = [self.input_mapping[q] for q in instruction.target]
            next_instruction = BraketInstructionWrapper(instruction, qubits)
            self.instructions.append(next_instruction)

    @property
    def num_qubits(self):
        return len(self.qubits)

    @property
    def package(self):
        return "braket"

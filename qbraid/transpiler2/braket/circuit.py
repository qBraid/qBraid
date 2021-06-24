from ..circuit import AbstractCircuitWrapper
from .instruction import BraketInstructionWrapper
from qbraid.exceptions import PackageError
from braket.circuits.circuit import Circuit


class BraketCircuitWrapper(AbstractCircuitWrapper):
    def __init__(self, circuit: Circuit):

        super().__init__()

        self.circuit = circuit
        self.qubits = circuit.qubits
        self.input_mapping = {q:i for i, q in enumerate(self.qubits)}
        self.instructions = []

        for instruction in circuit.instructions:

            qubits = [self.input_mapping[q] for q in instruction.target]
            next_instruction = BraketInstructionWrapper(instruction, qubits)
            self.instructions.append(next_instruction)

    @property
    def num_qubits(self):
        return len(self.qubits)

    @property
    def num_clbits(self):
        return len(self.clbitset)

    @property
    def supported_packages(self):
        return ["cirq", "qiskit", "braket"]


    def transpile(self, package: str):

        if package in self.supported_packages:
            if package == "braket":
                return self.circuit
            elif package == "cirq":
                from qbraid.transpiler2.cirq.outputs import circuit_to_cirq
                return circuit_to_cirq(self)
            elif package == "qiskit":
                from qbraid.transpiler2.qiskit.outputs import circuit_to_qiskit
                return circuit_to_qiskit(self)
            else:
                raise SystemError("transpile function does not reflect supported_packages")

        else:
            raise PackageError(package)

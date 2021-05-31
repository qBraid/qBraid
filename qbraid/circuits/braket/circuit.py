from ..circuit import AbstractCircuitWrapper
from ..qubitset import BraketQubitSet
from ..clbitset import ClbitSet
from .instruction import BraketInstructionWrapper
from qbraid.exceptions import PackageError
from braket.circuits.circuit import Circuit


class BraketCircuitWrapper(AbstractCircuitWrapper):
    def __init__(self, circuit: Circuit):

        super().__init__()

        self.circuit = circuit
        self.qubitset = BraketQubitSet([q for q in circuit.qubits])
        self.clbitset = ClbitSet()
        self.instructions = []

        for instruction in circuit.instructions:

            qubits = self.qubitset.get_qubits([q for q in instruction.target])
            clbits = []  # self.clbitset.get_clbits([q fo])
            next_instruction = BraketInstructionWrapper(instruction, qubits, clbits)
            self.instructions.append(next_instruction)

    @property
    def num_qubits(self):
        return len(self.qubitset)

    @property
    def num_clbits(self):
        return len(self.clbitset)

    @property
    def supported_packages(self):
        return ["cirq", "qiskit", "braket"]

    @property
    def _to_circuit(self) -> Circuit:

        output_circ = Circuit()

        # some instructions may be null (i.e. classically controlled gates, measurement)
        # these will return None, which should not be added to the circuit
        for instruction in self.instructions:
            instr = instruction.transpile("braket")
            if instr:
                output_circ.add_instruction(instr)

        return output_circ

    def transpile(self, package: str):

        if package in self.supported_packages:
            if package == "braket":
                return self.circuit
            elif package == "cirq":
                return self._to_cirq()
            elif package == "qiskit":
                return self._to_qiskit()
            else:
                raise SystemError("transpile function does not reflect supported_packages")

        else:
            raise PackageError(package)

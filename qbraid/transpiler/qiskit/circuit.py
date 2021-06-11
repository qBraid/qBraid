from ..circuit import AbstractCircuitWrapper
from ..clbitset import ClbitSet
from ..clbit import Clbit
from ..parameterset import QiskitParameterSet
from ..qubitset import QiskitQubitSet
from .instruction import QiskitInstructionWrapper
from qiskit.circuit import QuantumCircuit
from qbraid.exceptions import PackageError


class QiskitCircuitWrapper(AbstractCircuitWrapper):
    def __init__(self, circuit: QuantumCircuit):

        super().__init__()

        self.circuit = circuit
        self._outputs = {}
        self.qubitset = QiskitQubitSet(circuit.qubits)
        self.clbitset = ClbitSet(circuit.clbits)
        self.parameterset = QiskitParameterSet(circuit.parameters)
        self.instructions = []

        # create an Instruction object for each instruction in the circuit
        for instruction, qubit_list, clbit_list in circuit.data:

            qubits = self.qubitset.get_qubits(qubit_list)
            clbits = self.clbitset.get_clbits(clbit_list)
            params = self.parameterset.get_parameters(instruction.params)

            if len(clbits) > 0:
                assert isinstance(clbits[0], Clbit)

            next_instruction = QiskitInstructionWrapper(instruction, qubits, clbits, params)
            self.instructions.append(next_instruction)

    @property
    def num_qubits(self):
        return self.circuit.num_qubits

    @property
    def num_clbits(self):
        return self.circuit.num_clbits

    @property
    def supported_packages(self):
        return ["qiskit", "braket", "cirq"]

    def transpile(self, package: str):

        if package in self.supported_packages:
            if package == "braket":
                return self._to_braket()
            elif package == "cirq":
                return self._to_cirq()
            elif package == "qiskit":
                return self.circuit
            else:
                raise SystemError("transpile function does not reflect supported_packages")

        else:
            raise PackageError(package)

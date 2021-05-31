from abc import ABC
from braket.circuits.instruction import Instruction as BraketInstruction
from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure
from qiskit.circuit.measure import Measure as QiskitMeasure
from qbraid.exceptions import PackageError


class AbstractInstructionWrapper(ABC):
    def __init__(self):

        self.instruction = None
        self.qubits = []
        self.clbits = []
        self.package = None
        self.gate = None
        self.params = None

        self._outputs = {}

    def _to_braket(self):

        gate = self.gate.transpile("braket")
        qubits = [qubit.transpile("braket") for qubit in self.qubits]

        if gate == "BraketMeasure":
            return None
        else:
            return BraketInstruction(gate, qubits)

    def _to_cirq(self):

        qubits = [qubit.transpile("cirq") for qubit in self.qubits]
        gate = self.gate.transpile("cirq")

        if gate == "CirqMeasure":
            return CirqMeasure(*qubits, key=str(self.clbits[0].index))
        else:
            return gate(*qubits)

    def _to_qiskit(self):

        gate = self.gate.transpile("qiskit")
        qubits = [qubit.transpile("qiskit") for qubit in self.qubits]
        clbits = [clbit.output("qiskit") for clbit in self.clbits]

        if isinstance(gate, QiskitMeasure):
            return gate, qubits, clbits
        else:
            return gate, qubits, clbits

    def transpile(self, package: str):

        if package == "braket":
            return self._to_braket()
        elif package == "cirq":
            return self._to_cirq()
        elif package == "qiskit":
            return self._to_qiskit()
        else:
            raise PackageError(package)

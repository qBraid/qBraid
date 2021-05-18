from typing import Any, Sequence, Dict, Iterable, Union
from abc import ABC

from .clbitset import ClbitSet

from braket.circuits.instruction import Instruction as BraketInstruction
from qiskit.circuit import Instruction as QiskitInstruction
from qiskit.circuit.gate import Gate as QiskitGate
from cirq.ops.gate_operation import GateOperation as CirqGateInstruction
from cirq.ops.measure_util import measure as cirq_measure

# measurement gates
from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure
from qiskit.circuit.measure import Measure as QiskitMeasurementGate

InstructionInput = Union["BraketInstruction", "CirqGateInstruction", "QiskitInstruction"]


class AbstractInstructionWrapper(ABC):
    def __init__(self):

        self.instruction = None
        self.qubits = []
        self.clbits = []
        self.package = None
        self.gate = None
        self.params = None

        self._outputs = {}

    def _to_cirq(self):

        qubits = [qubit.transpile("cirq") for qubit in self.qubits]
        gate = self.gate.transpile("cirq")

        if gate == "CirqMeasure":
            return cirq_measure(qubits[0], key=self.clbits[0].index)
        else:
            return gate(*qubits)

    def _to_qiskit(self):

        gate = self.gate.transpile("qiskit")
        qubits = [qubit.transpile("qiskit") for qubit in self.qubits]
        clbits = [clbit.output("qiskit") for clbit in self.clbits]

        # assert np.log2(len(self.gate.matrix)) == len(qubits)

        # if isinstance(gate, (QiskitCXGate, QiskitCCXGate)):
        #    print(gate, qubits)

        if isinstance(gate, QiskitMeasurementGate):
            return gate, qubits, clbits
        else:
            return gate, qubits, clbits

    def _to_braket(self):

        gate = self.gate.transpile("braket")
        qubits = [qubit.transpile("braket") for qubit in self.qubits]

        if gate == "BraketMeasure":
            return None
        else:
            return BraketInstruction(gate, qubits)

    def transpile(self, package: str):

        if package == "qiskit":
            return self._to_qiskit()
        elif package == "braket":
            return self._to_braket()
        elif package == "cirq":
            return self._to_cirq()
        else:
            print("Unable to transpile from {} to {}".format(self.package, package))

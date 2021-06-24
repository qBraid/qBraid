from ..circuit import AbstractCircuitWrapper
from ..qubitset import CirqQubitSet
from ..clbitset import ClbitSet
from ..clbit import Clbit
from .instruction import CirqInstructionWrapper
from ..qbraid.gate import QbraidGateWrapper
from ..qbraid.instruction import QbraidInstructionWrapper
from qbraid.exceptions import PackageError

from cirq.circuits import Circuit
from cirq.ops.measurement_gate import MeasurementGate


class CirqCircuitWrapper(AbstractCircuitWrapper):
    def __init__(self, circuit: Circuit, exact_time: bool = False):

        super().__init__()

        self.circuit = circuit
        self.qubits = circuit.all_qubits()
        self.input_mapping = {qubit:index for index, qubit in enumerate(self.qubits)}
        
        for op in circuit.all_operations():
            
            qbs = [self.input_mapping[qubit] for qubit in op.qubits]
            next_instruction = CirqInstructionWrapper(op,qbs)
            self.instructions.append(next_instruction)

    @property
    def num_qubits(self):
        return len(self.qubits)

    @property
    def supported_packages(self):
        return ["cirq", "qiskit", "braket"]

    @property
    def _to_circuit(self, auto_measure=False):

        output_circ = Circuit()

        for instruction in self.instructions:
            transp_instr = instruction.transpile("cirq")
            output_circ.append(transp_instr)

        # auto measure
        if auto_measure:
            for index, qubit in enumerate(self.qubitset.qubits):
                clbit = Clbit(index)
                instruction = QbraidInstructionWrapper(
                    QbraidGateWrapper(gate_type="MEASURE"), [qubit], [clbit]
                )
                transp_instr = instruction.transpile("cirq")
                output_circ.append(transp_instr)

        return output_circ

    def transpile(self, package: str):

        if package in self.supported_packages:
            if package == "braket":
                from qbraid.transpiler2.braket.outputs import circuit_to_braket
                return circuit_to_braket(self)
            elif package == "cirq":
                return self.circuit
            elif package == "qiskit":
                from qbraid.transpiler2.qiskit.outputs import circuit_to_qiskit
                return circuit_to_qiskit(self)
            else:
                raise SystemError("transpile function does not reflect supported_packages")

        else:
            raise PackageError(package)



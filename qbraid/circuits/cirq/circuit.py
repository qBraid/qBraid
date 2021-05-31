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
        self.qubitset = CirqQubitSet(circuit.all_qubits())
        self.clbitset = ClbitSet()

        if not exact_time:
            self.instructions = []
            for op in circuit.all_operations():

                # identify the qBraid Qubit objects associated with the operation
                qubits = self.qubitset.get_qubits(op.qubits)

                # handle measurement operations and gate operations seperately
                if isinstance(op.gate, MeasurementGate):

                    # create Clbit object based on the info from the measurement operation
                    output_index = int(op.gate.key)
                    assert isinstance(output_index, int)
                    new_clbit = Clbit(output_index)

                    # create the list of clbits for the operation (in this case just the one)
                    clbits = [new_clbit]
                    # add to the ClbitSet associated with the whole circuit
                    self.clbitset.append(new_clbit)

                else:
                    clbits = []

                # create an instruction object and add it to the list
                next_instruction = CirqInstructionWrapper(op, qubits, clbits)
                self.instructions.append(next_instruction)
        else:
            raise NotImplementedError
            # self.moments = [Moment(moment) for moment in circuit.moments]

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
                return self._to_braket()
            elif package == "cirq":
                return self.circuit
            elif package == "qiskit":
                return self._to_qiskit()
            else:
                raise SystemError("transpile function does not reflect supported_packages")

        else:
            raise PackageError(package)

from ..circuit import AbstractCircuitWrapper
from ..qubitset import CirqQubitSet
from ..clbitset import ClbitSet
from ..clbit import Clbit

# from ..parameterset import CirqParameterSet
from .instruction import CirqInstructionWrapper

from cirq.circuits import Circuit as CirqCircuit
from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure


class CirqCircuitWrapper(AbstractCircuitWrapper):
    def __init__(self, circuit: CirqCircuit, exact_time: bool = False):

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
                if isinstance(op.gate, CirqMeasure):

                    # create Clbit object based on the info from the measurement operation
                    output_index = op.gate.key
                    assert isinstance(output_index, int)
                    new_clbit = Clbit(output_index)

                    # create the list of clbits for the operation (in this case just the one)
                    clbits = [new_clbit]
                    # add to the ClbitSet associated with the whole circuit
                    self.clbitset.append(new_clbit)

                else:
                    clbits = []

                # create an instruction object and add it to the list
                self.instructions.append(CirqInstructionWrapper(op, qubits, clbits))
        else:
            pass
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

    def transpile(self, package: str):

        if package in self.supported_packages:
            if package == "qiskit":
                return self._to_qiskit()
            elif package == "braket":
                return self._to_braket()
            elif package == "cirq":
                return self.circuit

        else:
            print("The transpiler does not support conversion from cirq to {}.".format(package))

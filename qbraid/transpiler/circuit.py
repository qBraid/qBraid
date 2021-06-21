import abc
from abc import ABC
from .clbit import Clbit
from .qbraid.gate import QbraidGateWrapper
from .qbraid.instruction import QbraidInstructionWrapper
from typing import Union

from braket.circuits.circuit import Circuit as BraketCircuit
from cirq.circuits import Circuit as CirqCircuit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.circuit.classicalregister import (
    ClassicalRegister as QiskitClassicalRegister,
)

SupportedCircuit = Union[BraketCircuit, CirqCircuit, QiskitCircuit]


class AbstractCircuitWrapper(ABC):
    def __init__(self):

        self.qubitset = None
        self.clbitset = None
        self.instructions = []

    @property
    @abc.abstractmethod
    def num_qubits(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def num_clbits(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def supported_packages(self) -> list:
        pass

    @abc.abstractmethod
    def transpile(self, package: str) -> SupportedCircuit:
        pass

    def _to_braket(self) -> BraketCircuit:

        output_circ = BraketCircuit()

        # some instructions may be null (i.e. classically controlled gates, measurement)
        # these will return None, which should not be added to the circuit
        for instruction in self.instructions:
            instr = instruction.transpile("braket")
            if instr:
                output_circ.add_instruction(instr)

        return output_circ

    def _to_cirq(self, auto_measure=False) -> CirqCircuit:

        output_circ = CirqCircuit()

        for instruction in self.instructions:
            output_circ.append(instruction.transpile("cirq"))

        # auto measure
        if auto_measure:
            for index, qubit in enumerate(self.qubitset.qubits):
                clbit = Clbit(index)
                instruction = QbraidInstructionWrapper(
                    QbraidGateWrapper(gate_type="MEASURE"), [qubit], [clbit]
                )
                output_circ.append(instruction.transpile("cirq"))

        return output_circ

    def _to_qiskit(self, auto_measure=False) -> QiskitCircuit:

        qreg = self.qubitset.transpile("qiskit")

        if self.num_clbits:
            creg = self.clbitset.transpile("qiskit")
            # creg = QiskitClassicalRegister(self.num_clbits)
            output_circ = QiskitCircuit(qreg, creg, name="qBraid_transpiler_output")
        elif auto_measure:
            creg = QiskitClassicalRegister(self.num_qubits)
            output_circ = QiskitCircuit(qreg, creg, name="qBraid_transpiler_output")
        else:
            output_circ = QiskitCircuit(qreg, name="qBraid_transpiler_output")

        # add instructions
        for instruction in self.instructions:
            # assert np.log2(len(instruction.gate.matrix)) == len(instruction.qubits)
            output_circ.append(*instruction.transpile("qiskit"))

        # auto measure
        if auto_measure:
            raise NotImplementedError

        return output_circ

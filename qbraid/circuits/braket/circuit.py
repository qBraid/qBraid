from ..circuit import AbstractCircuitWrapper
from ..qubitset import BraketQubitSet
from ..clbitset import ClbitSet
from ..clbit import Clbit
from .instruction import BraketInstructionWrapper

from braket.circuits.circuit import Circuit as BraketCircuit


class BraketCircuitWrapper(AbstractCircuitWrapper):
    def __init__(self, circuit: BraketCircuit):

        super().__init__()

        self.qubitset = BraketQubitSet([q for q in circuit.qubits])
        self.clbitset = ClbitSet()

        self.instructions = []

        for instruction in circuit.instructions:

            qubits = self.qubitset.get_qubits([q for q in instruction.target])
            clbits = []  # self.clbitset.get_clbits([q fo])

            self.instructions.append(
                BraketInstructionWrapper(instruction, qubits, clbits)
            )

    @property
    def num_qubits(self):
        pass

    @property
    def num_clbits(self):
        pass

    @property
    def supported_packages(self):
        return ["cirq", "qiskit", "braket"]

    def transpile(self, package: str):

        if package in self.supported_packages:
            if package == "qiskit":
                return self._to_qiskit()
            elif package == "cirq":
                return self._to_cirq()
            elif package == "braket":
                return self.circuit

        else:
            print(
                "The transpiler does not support conversion from cirq to {}.".format(
                    package
                )
            )

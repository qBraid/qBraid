from typing import List

from braket.circuits.circuit import Circuit

from qbraid.transpiler.circuit import CircuitWrapper
from .instruction import BraketInstructionWrapper
from .moment import BraketMomentWrapper


class BraketCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: Circuit, input_qubit_mapping=None):
        super().__init__(circuit, input_qubit_mapping)

        self._qubits = circuit.qubits
        self._num_qubits = len(self.qubits)
        self._package = "braket"

    @property
    def moments(self) -> List[BraketMomentWrapper]:
        pass

    @property
    def instructions(self) -> List[BraketInstructionWrapper]:

        instructions = []
        for instruction in self.circuit.instructions:
            qubits = [self.input_qubit_mapping[q] for q in instruction.target]
            next_instruction = BraketInstructionWrapper(instruction, qubits)
            instructions.append(next_instruction)

        return instructions



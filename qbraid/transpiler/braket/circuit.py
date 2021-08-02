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

        if not input_qubit_mapping:
            input_qubit_mapping = {q:i for i,q in enumerate(self._qubits)}

        self._wrap_circuit(circuit, input_qubit_mapping)

    def _wrap_circuit(self, circuit, input_qubit_mapping):

        self._circuit

        instructions = []
        for instruction in circuit.instructions:
            qubits = [input_qubit_mapping[q] for q in instruction.target]
            next_instruction = BraketInstructionWrapper(instruction, qubits)
            instructions.append(next_instruction)

        self._instructions =  instructions

    @property
    def moments(self) -> None:
        return None

    @property
    def instructions(self) -> List[BraketInstructionWrapper]:
        if hasattr(self,'_instructions'):
            return self._instructions
        return list()

        



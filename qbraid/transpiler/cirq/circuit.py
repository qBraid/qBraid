from typing import List

from cirq.circuits import Circuit

from qbraid.transpiler.circuit import CircuitWrapper
from .instruction import CirqInstructionWrapper


class CirqCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: Circuit, input_qubit_mapping=None):
        super().__init__(circuit, input_qubit_mapping)

        self._qubits = circuit.all_qubits()
        self._num_qubits = len(self.qubits)
        self._package = "cirq"

    @property
    def instructions(self) -> List[CirqInstructionWrapper]:

        params = set()
        instructions = []
        for op in self.circuit.all_operations():
            qbs = [self.input_qubit_mapping[qubit] for qubit in op.qubits]
            next_instruction = CirqInstructionWrapper(op, qbs)
            params.union(set(next_instruction.gate.get_abstract_params()))
            instructions.append(next_instruction)

        input_param_mapping = {param: index for index, param in enumerate(self.params)}

        for instruction in instructions:
            instruction.gate.parse_params(self.input_param_mapping)

        self._params = params
        self._input_param_mapping = input_param_mapping
        return instructions

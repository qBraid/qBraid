from typing import List

from qiskit.circuit import Parameter
from qiskit.circuit import QuantumCircuit as Circuit

from qbraid.transpiler.circuit import CircuitWrapper
from qbraid.transpiler.parameter import ParamID

from .instruction import QiskitInstructionWrapper


class QiskitCircuitWrapper(CircuitWrapper):

    """Qiskit implementation of the abstract CircuitWrapper class"""

    def __init__(self, circuit: Circuit, input_qubit_mapping=None):
        super().__init__(circuit, input_qubit_mapping)

        self._qubits = circuit.qubits
        self._params = circuit.parameters
        self._num_qubits = circuit.num_qubits
        self._num_clbits = circuit.num_clbits
        self._input_param_mapping = {p: ParamID(i, p.name) for i, p in enumerate(self.params)}
        self.output_qubit_mapping = {}
        self._package = "qiskit"

    @property
    def instructions(self) -> List[QiskitInstructionWrapper]:
        instructions = []
        for instruction, qubit_list, clbit_list in self.circuit.data:
            qubits = [self.input_qubit_mapping[q] for q in qubit_list]
            param_list = instruction.params
            params = [
                self.input_param_mapping[p] if isinstance(p, Parameter) else p for p in param_list
            ]
            next_instruction = QiskitInstructionWrapper(instruction, qubits, params=params)
            instructions.append(next_instruction)

        return instructions

    @property
    def moments(self):
        return None

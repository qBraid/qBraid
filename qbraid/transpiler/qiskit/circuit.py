from qiskit.circuit import Parameter
from qiskit.circuit import QuantumCircuit

from qbraid.transpiler.parameter import ParamID
from qbraid.transpiler.circuit import CircuitWrapper
from .instruction import QiskitInstructionWrapper


class QiskitCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: QuantumCircuit, input_qubit_mapping=None):

        super().__init__()

        self.circuit = circuit
        self.qubits = circuit.qubits
        if input_qubit_mapping:
            self.input_qubit_mapping = input_qubit_mapping
        else:
            self.input_qubit_mapping = {qubit: index for index, qubit in enumerate(self.qubits)}
        self.output_qubit_mapping = {}

        # self.parameterset = QiskitParameterSet(circuit.parameters)
        self.input_param_mapping = {
            param: ParamID(index, param.name) for index, param in enumerate(circuit.parameters)
        }
        self.params = self.input_param_mapping.values()

        self.instructions = []

        # create an Instruction object for each instruction in the circuit
        for instruction, qubit_list, clbit_list in circuit.data:

            qubits = [self.input_qubit_mapping[qubit] for qubit in qubit_list]

            param_list = instruction.params
            params = [
                self.input_param_mapping[p] if isinstance(p, Parameter) else p for p in param_list
            ]

            next_instruction = QiskitInstructionWrapper(instruction, qubits, params=params)
            self.instructions.append(next_instruction)

        self._package = "qiskit"

    @property
    def num_qubits(self):
        return self.circuit.num_qubits

    @property
    def num_clbits(self):
        return self.circuit.num_clbits

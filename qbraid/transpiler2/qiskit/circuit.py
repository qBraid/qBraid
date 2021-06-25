from ..circuit import AbstractCircuitWrapper
from ..utils import supported_packages
from ..parameterset import QiskitParameterSet
from .instruction import QiskitInstructionWrapper
from qiskit.circuit import QuantumCircuit, Parameter
from qbraid.exceptions import PackageError


class QiskitCircuitWrapper(AbstractCircuitWrapper):
    def __init__(self, circuit: QuantumCircuit):

        super().__init__()

        self.circuit = circuit
        self._outputs = {}
        self.qubits = circuit.qubits
        self.input_qubit_mapping = {qubit:index for index, qubit in enumerate(self.qubits)}
        
        #self.parameterset = QiskitParameterSet(circuit.parameters)
        self.params = circuit.parameters
        self.input_param_mapping = {param:index for index, param in enumerate(self.params)}
        
        self.instructions = []

        # create an Instruction object for each instruction in the circuit
        for instruction, qubit_list, clbit_list in circuit.data:

            qubits = [self.input_qubit_mapping[qubit] for qubit in qubit_list]
            
            param_list = instruction.params
            params = [self.input_param_mapping[param] for param in param_list if isinstance(param,Parameter)]

            next_instruction = QiskitInstructionWrapper(instruction, qubits, params=params)
            self.instructions.append(next_instruction)

    @property
    def num_qubits(self):
        return self.circuit.num_qubits

    @property
    def num_clbits(self):
        return self.circuit.num_clbits

    @property
    def package(self):
        return 'qiskit'
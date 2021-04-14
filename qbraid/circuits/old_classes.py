# old classes

class QubitSet():
    
    """
    A wrapper class for a collection of qBraid Qubit objects.
    
    Arguments:
        qubits: A wrapper class for a list of qubits. 
        
    Attributes:
        qubits (list[Qubit]): list of qBraid Qubit objects
        outputs (dict): output objects generated for any or all other packages
        get_qubits(list[QubitInput]): 
    Methods:
        get_qubit: searches the list of qubits for the qBraid Qubit object 
            which corresponds to the qubit object from any package
        get_qubits: same as get_qubit but for a list of qubits to find
        output: transpile the set of qubits to a corresponding package.
            currently only implemented for qiskit

    """
    
    def __init__(self, qubits: Iterable[Qubit] = None):
        
        self.qubits = [Qubit(qubit) for qubit in qubits]

    def __len__(self):
        return len(self.qubits)

    def get_qubit_by_id(self, indentifier: Union[str,int]):
        
        for qubit in self.qubits:
            if qubit.id == identifier:
                return qubit
        return "Could not find qubit with id: {}".format(identifier)
    
    def get_qubits(self, targetqubits: Iterable):
        
        """
        search for the qBraid Qubit object in the QubitSet that corresponds to
        each qubit object in the input list
        """
        
        return [self.get_qubit(qubit) for qubit in targetqubits]
    
    def get_qubit(self, targetqubit: QubitInput):
        
        """
        search for the qBraid Qubit object in the QubitSet that corresponds to
        to the passed qubit
        """
        
        for qbraid_qubit in self.qubits:
            if qbraid_qubit.qubit == targetqubit:
                assert type(qbraid_qubit) == Qubit
                return qbraid_qubit
            
    def output(self, output_type: str):
        
        if output_type == 'qiskit':
            
            for index, qubit in enumerate(self.qubits):
                qubit.outputs['qiskit'] = index
                
            return self._to_qiskit()
        
        else:
            pass
                
    def _to_qiskit(self):
        return QiskitQuantumRegister(len(self.qubits))
    
class OldInstruction():
    
    """
    qBraid Instruction class
    
    Arguments:
        instruction:
    
    Attributes:
        instruction: the original instruction as originally passed in
        qubits: a list of qBraid Qubit() objects involved in the operation
        clbits: a list of qBraid Clbit() objects involved in the operation
            these are predominately used for measurement
        
    Methods:
        output (package): returns a transpiled object of the desired type
         
    """
    
    def __init__(self, instruction: InstructionInput = None, qubits: Iterable = None, clbits: Iterable =None):
        
        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        
        if isinstance(instruction,BraketInstruction):
            self.package = 'braket'
            self.gate = Gate(instruction.operator)
        
        elif isinstance(instruction,QiskitInstruction):
            self.package = 'qiskit'
            self.gate = Gate(instruction)
            
        elif isinstance(instruction,CirqGateInstruction):
            self.package = 'cirq'
            self.gate = Gate(instruction.gate)
        
        elif isinstance(instruction, Gate):
            self.gate = instruction
        
    def _to_cirq(self):
        
        #print(self.qubits)
        qubits = [qubit.output('cirq') for qubit in self.qubits]
        gate = self.gate.output('cirq')
        
        if gate == 'CirqMeasure':
            return cirq_measure(qubits[0],key=self.clbits[0].index)
        else:
            return gate(*qubits)
        
    def _to_qiskit(self):
        
        gate = self.gate.output('qiskit')
        qubits = [qubit.output('qiskit') for qubit in self.qubits]
        clbits = [clbit.output('qiskit') for clbit in self.clbits]
        
        if isinstance(gate, QiskitMeasurementGate):
            return gate, qubits, clbits
        else:
            return gate,qubits,clbits
    
    def _to_braket(self):
        
        gate = self.gate.output('braket')
        qubits = [qubit.output('braket') for qubit in self.qubits]
        
        if gate == 'BraketMeasure':
            return None
        else:
            return BraketInstruction(gate,qubits)
    
    def output(self, package: str):
        
        if package == 'cirq':
            return self._to_cirq()
        elif package == 'qiskit':
            return self._to_qiskit()
        elif package == 'braket':
            return self._to_braket()
            
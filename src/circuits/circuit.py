from typing import Any, Sequence, Dict, Iterable, Union


#qbraid imports
from qubit import Qubit
from instruction import Instruction
from moment import Moment
from qubitset import QubitSet
from clbitset import ClbitSet

from braket.circuits.circuit import Circuit as BraketCircuit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from cirq.circuits import Circuit as CirqCircuit



#types 
CircuitInput = Union["BraketCircuit", "CirqCircuit", "QiskitCircuit", 
                        Iterable[Moment], Iterable[Instruction]]

class Circuit():
    
    """
        Create a QbraidCircuit object.
        
        Wrapper object for any number of possible circuit objects, including:
            Cirq: Circuit()
            Qiskit: QuantumCircuit()
            Braket: Circuit()
            
        Args:
            circuit: the circuit object
        
        Attributes:
            circuit: the actual circuit object
            qubitset: a QubitSet object
            clbitset: a ClbitSet object
            instructions: a list of Instruction objects
            moments: a list of Moment objects (optional)
        
        Methods:
            num_qubits:
            num_clbits:
            output: returns a circuit object of a different type
        
        Raises:
            typeError: if the circuit object is not a supported type
            
        Examples:
            
     """       
    
    def __init__(self, circuit: CircuitInput = None, exact_time: str = False):
        
        """
        Create a new Circuit object
        
        Args:
            circuit (CircuitInput): the circuit
            exact_time: whether to parse the instructions as moments (applies to cirq circuits)
        """
        
        self.circuit = circuit
        self.clbitset = ClbitSet()
        
        if isinstance(circuit, BraketCircuit):
            pass
        
        elif isinstance(circuit,QiskitCircuit):
            
            self.qubitset = QubitSet(circuit.qubits)

            
            self.instructions = []
            
            #create an Instruction object for each instruction in the circuit
            for instruction, qubit_list, clbit_list in circuit.data:
                
                qubits = self.qubitset.get_qubits(qubit_list)
                clbits = []

                self.instructions.append(Instruction(instruction,qubits,clbits))
            
        elif isinstance(circuit, CirqCircuit):
            
            self.qubitset = QubitSet(circuit.all_qubits())
            
            if exact_time:
                self.moments = [Moment(moment) for moment in circuit.moments]
                #other data storage stuff
            
            else:
                self.instructions = []
                for op in circuit.all_operations():
                    
                    qubits = self.qubitset.get_qubits(op.qubits)
                    clbits = []
                    
                    self.instructions.append(Instruction(op,qubits,clbits))
    
    def num_qubits(self):
        return len(self.qubitset)
    
    def num_clbits(self):
        return len(self.clbitset)
    
    def output(self, output_package = None):

        """
        Returns a circuit object of a different type
        
        Args:
            output_class: options are cirq, qiskit, etc.
        """
        
        if output_package == 'cirq':
            return self.to_cirq()
        elif output_package == 'qiskit':
            return self.to_qiskit()
    
    def to_cirq(self):
        
        output_circ = CirqCircuit()
        
        for instruction in self.instructions:
            output_circ.append(instruction.to_cirq())
        
        return output_circ
        
    def to_qiskit(self):
        
        qreg = self.qubitset.output('qiskit')
        
        if self.num_clbits():
            creg = ClassicalRegister(self.num_clbits())
            output_circ = QiskitCircuit(qreg,creg,name='qBraid_transpiler_output')
        else: 
            output_circ = QiskitCircuit(qreg)    
        
        for instruction in self.instructions:
            output_circ.append(*instruction.to_qiskit())
        
        return output_circ
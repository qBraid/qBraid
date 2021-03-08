from typing import Any, Sequence, Dict, Iterable, Union

#import qBraid
from qubit import Qubit
#from .qubit import Qubit
from instruction import Instruction
from moment import Moment
from qubitset import QubitSet
from clbitset import ClbitSet
from clbit import Clbit
from gate import Gate

from braket.circuits.circuit import Circuit as BraketCircuit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from cirq.circuits import Circuit as CirqCircuit

from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure

from qiskit.circuit.classicalregister import ClassicalRegister as QiskitClassicalRegister

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
            num_qubits:mnm   
            num_clbits:
            output: returns a circuit object of a different type
        
        Raises:
            typeError: if the circuit object is not a supported type
            
        Examples:
            
     """       
    
    def __init__(self, 
                 circuit: CircuitInput = None, 
                 exact_time: str = False,
                 auto_measure: bool = False
                 ):
        
        """
        Create a new Circuit object
        
        Args:
            circuit (CircuitInput): the circuit
            exact_time: whether to parse the instructions as moments (applies to cirq circuits)
        """
        
        self.circuit = circuit
        
        #other properties
        self.auto_measure = auto_measure
        
        if isinstance(circuit, BraketCircuit):
            
            self.qubitset = QubitSet([q for q in circuit.qubits])
            self.clbitset = ClbitSet()
        
            self.instructions = []
            for instruction in circuit.instructions:
                
                qubits = self.qubitset.get_qubits([q for q in instruction.target])
                clbits = [] #self.clbitset.get_clbits([q fo])
                
                self.instructions.append(Instruction(instruction,qubits,clbits))
        
        elif isinstance(circuit,QiskitCircuit):
            
            self.qubitset = QubitSet(circuit.qubits)
            self.clbitset = ClbitSet(circuit.clbits)
            
            self.instructions = []
            
            #create an Instruction object for each instruction in the circuit
            for instruction, qubit_list, clbit_list in circuit.data:
                
                qubits = self.qubitset.get_qubits(qubit_list)
                clbits = self.clbitset.get_clbits(clbit_list)
                if len(clbits)>0:
                    assert(isinstance(clbits[0], Clbit))

                self.instructions.append(Instruction(instruction,qubits,clbits))
            
        elif isinstance(circuit, CirqCircuit):
            
            self.qubitset = QubitSet(circuit.all_qubits())
            self.clbitset = ClbitSet()
            
            if exact_time:
                self.moments = [Moment(moment) for moment in circuit.moments]
                #other data storage stuff
            
            else:
                self.instructions = []
                for op in circuit.all_operations():
                    
                    #identify the qBraid Qubit objects associated with the operation
                    qubits = self.qubitset.get_qubits(op.qubits)
                    
                    #handle measurement operations and gate operations seperately
                    if isinstance(op.gate, CirqMeasure):
                        
                        # create Clbit object based on the info from the measurement operation
                        output_index = op.gate.key
                        assert isinstance(output_index, int)
                        new_clbit = Clbit(output_index)
                        
                        #create the list of clbits for the operation (in this case just the one)
                        clbits = [new_clbit]
                        #add to the ClbitSet associated with the whole circuit
                        self.clbitset.append(new_clbit)
                    
                    else:
                        clbits = []
                    
                    #create an instruction object and add it to the list
                    self.instructions.append(Instruction(op,qubits,clbits))
    
    
    
    def num_qubits(self):
        return len(self.qubitset)
    
    def num_clbits(self):
        return len(self.clbitset)
    
    def output(self, output_package: str = None):

        """
        Returns a circuit object of a different type
        
        #change to get_circuit()
        
        Args:
            output_class: options are cirq, qiskit, etc.
        """
        
        if output_package == 'cirq':
            return self._to_cirq()
        elif output_package == 'qiskit':
            return self._to_qiskit()
        elif output_package == 'braket':
            return self._to_braket()
    
    def _to_cirq(self):
        
        output_circ = CirqCircuit()
        
        for instruction in self.instructions:
            output_circ.append(instruction.output('cirq'))
        
        #auto measure
        if self.auto_measure:
            for index, qubit in enumerate(self.qubitset.qubits):
                clbit = Clbit(index)
                instruction = Instruction(Gate(gate_type='MEASURE'),[qubit],[clbit])
                output_circ.append(instruction.output('cirq'))
        
        return output_circ
        
    def _to_qiskit(self):
        
        qreg = self.qubitset.output('qiskit')
        
        if self.num_clbits():
            creg = QiskitClassicalRegister(self.num_clbits())
            output_circ = QiskitCircuit(qreg,creg,name='qBraid_transpiler_output')
        elif self.auto_measure:
            creg = QiskitClassicalRegister(self.num_qubits())
            output_circ = QiskitCircuit(qreg,creg,name='qBraid_transpiler_output')
        else: 
            output_circ = QiskitCircuit(qreg, name='qBraid_transpiler_output')    
        
        # add instructions
        for instruction in self.instructions:
            output_circ.append(*instruction.output('qiskit'))
        
        #auto measure
        if self.auto_measure:
            pass
        
        return output_circ
    
    def _to_braket(self):
        
        output_circ = BraketCircuit()
        
        #some instructions may be null (i.e. classically controlled gates, measurement)
        #these will return None, which should not be added to the circuit
        for instruction in self.instructions:
            instr = instruction.output('braket')
            if instr:
                output_circ.add_instruction(instr)
            
        return output_circ
    
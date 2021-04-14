from typing import Any, Sequence, Dict, Iterable, Union
import abc
from abc import ABC, abstractmethod
import numpy as np

#import qBraid
from .qubit import Qubit
from .instruction import (QiskitInstructionWrapper, BraketInstructionWrapper,
                          CirqInstructionWrapper, QbraidInstructionWrapper)
from .moment import Moment
from .qubitset import (QiskitQubitSet, CirqQubitSet, BraketQubitSet)
from .clbitset import ClbitSet
from .clbit import Clbit
from .gate import QbraidGateWrapper
from .parameterset import QiskitParameterSet, CirqParameterSet

from braket.circuits.circuit import Circuit as BraketCircuit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from cirq.circuits import Circuit as CirqCircuit

from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure

from qiskit.circuit.classicalregister import ClassicalRegister as QiskitClassicalRegister


class AbstractCircuitWrapper(ABC):
    
    def __init__(self):
        
        self.instructions = []
    
    @abc.abstractproperty
    def num_qubits():
        pass
    
    @abc.abstractproperty
    def num_clbits():
        pass
    
    @abc.abstractproperty
    def supported_packages():
        pass
    
    def transpile(self):
        pass
    
    def _to_cirq(self, auto_measure = False):
        
        output_circ = CirqCircuit()
        
        for instruction in self.instructions:
            output_circ.append(instruction.transpile('cirq'))
        
        #auto measure
        if auto_measure:
            for index, qubit in enumerate(self.qubitset.qubits):
                clbit = Clbit(index)
                instruction = QbraidInstructionWrapper(QbraidGateWrapper(gate_type='MEASURE'),[qubit],[clbit])
                output_circ.append(instruction.transpile('cirq'))
        
        return output_circ
        
    def _to_qiskit(self, auto_measure = False):
        
        qreg = self.qubitset.transpile('qiskit')
        
        if self.num_clbits:
            creg = QiskitClassicalRegister(self.num_clbits)
            output_circ = QiskitCircuit(qreg,creg,name='qBraid_transpiler_output')
        elif auto_measure:
            creg = QiskitClassicalRegister(self.num_qubits)
            output_circ = QiskitCircuit(qreg,creg,name='qBraid_transpiler_output')
        else: 
            output_circ = QiskitCircuit(qreg, name='qBraid_transpiler_output')    
        
        # add instructions
        for instruction in self.instructions:
            assert np.log2(len(instruction.gate.matrix)) == len(instruction.qubits)
            output_circ.append(*instruction.transpile('qiskit'))
        
        #auto measure
        if auto_measure:
            pass
        
        return output_circ 
    
    def _to_braket(self):
        
        output_circ = BraketCircuit()
        
        #some instructions may be null (i.e. classically controlled gates, measurement)
        #these will return None, which should not be added to the circuit
        for instruction in self.instructions:
            instr = instruction.transpile('braket')
            if instr:
                output_circ.add_instruction(instr)
            
        return output_circ
    
    
    
class QiskitCircuitWrapper(AbstractCircuitWrapper):
    
    def __init__(self, circuit: QiskitCircuit):
        
        super().__init__
        
        self.circuit = circuit
        self._outputs = {}
        
        self.qubitset = QiskitQubitSet(circuit.qubits)
        self.clbitset = ClbitSet(circuit.clbits)
        self.parameterset = QiskitParameterSet(circuit.parameters)
        print(list(type(i) for i in self.parameterset.parameters))
        
        self.instructions = []
        
        #create an Instruction object for each instruction in the circuit
        for instruction, qubit_list, clbit_list in circuit.data:
            
            qubits = self.qubitset.get_qubits(qubit_list)
            clbits = self.clbitset.get_clbits(clbit_list)
            params = self.parameterset.get_parameters(instruction.params)
            
            if len(clbits)>0:
                assert(isinstance(clbits[0], Clbit))

            self.instructions.append(QiskitInstructionWrapper(instruction,qubits,clbits,params))
    
    @property
    def num_qubits(self):    
        return self.circuit.num_qubits
    
    @property
    def num_clbits(self):
        return self.circuit.num_clbits
    
    @property
    def supported_packages(self):
        return ['qiskit','braket','cirq']
    
    def transpile(self,package:str):

        if package in self.supported_packages:
            if package == 'cirq':    
                return self._to_cirq()
            elif package == 'braket':
                return self._to_braket()
            elif package == 'qiskit':
                return self.circuit
        
        else:
            print("The transpiler does not support conversion from qiskit to {}.".format(package))
        
    

class CirqCircuitWrapper(AbstractCircuitWrapper):
    
    def __init__(self, circuit: CirqCircuit, exact_time: bool = False):
        
        super().__init__()
        
        self.circuit = circuit
        
        self.qubitset = CirqQubitSet(circuit.all_qubits())
        self.clbitset = ClbitSet()
            
        if not exact_time:
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
                self.instructions.append(CirqInstructionWrapper(op,qubits,clbits))
        else:
            pass
            #self.moments = [Moment(moment) for moment in circuit.moments]
            
    @property
    def num_qubits(self):
        return len(self.qubitset)
    
    @property
    def num_clbits(self):
        return len(self.clbitset)
    
    @property
    def supported_packages(self):
        return ['cirq','qiskit','braket']
    
    def transpile(self,package:str):

        if package in self.supported_packages:
            if package == 'qiskit':    
                return self._to_qiskit()
            elif package == 'braket':
                return self._to_braket()
            elif package == 'cirq':
                return self.circuit
        
        else:
            print("The transpiler does not support conversion from cirq to {}.".format(package))   

class BraketCircuitWrapper(AbstractCircuitWrapper):
    
    def __init__(self, circuit: BraketCircuit):
        
        super().__init__()
        
        self.qubitset = BraketQubitSet([q for q in circuit.qubits])
        self.clbitset = ClbitSet()
    
        self.instructions = []
        
        for instruction in circuit.instructions:
            
            qubits = self.qubitset.get_qubits([q for q in instruction.target])
            clbits = [] #self.clbitset.get_clbits([q fo])
            
            self.instructions.append(BraketInstructionWrapper(instruction,qubits,clbits))

    @property
    def num_qubits(self):
        pass
    
    @property
    def num_clbits(self):
        pass
    
    @property
    def supported_packages(self):
        return ['cirq','qiskit','braket']

    def transpile(self, package:str):

        if package in self.supported_packages:
            if package == 'qiskit':    
                return self._to_qiskit()
            elif package == 'cirq':
                return self._to_cirq()
            elif package == 'braket':
                return self.circuit
        
        else:
            print("The transpiler does not support conversion from cirq to {}.".format(package))   

CircuitInput = None

class OldCircuit():
    
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
    

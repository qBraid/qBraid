from typing import Any, Sequence, Dict, Iterable, Union
import numpy as np


from gate import Gate
from qubitset import QubitSet
from clbitset import ClbitSet

from braket.circuits.instruction import Instruction as BraketInstruction
from qiskit.circuit import Instruction as QiskitInstruction
from qiskit.circuit.gate import Gate as QiskitGate
from cirq.ops.gate_operation import GateOperation as CirqGateInstruction
from cirq.ops.measure_util import measure as cirq_measure

#measurement gates
from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure
from qiskit.circuit.measure import Measure as QiskitMeasurementGate

InstructionInput = Union["BraketInstruction", 
                         "CirqGateInstruction",
                         "QiskitInstruction"]

class Instruction():
    
    """
    qBraid Instruction class
    
    Arguments:
        instruction:
    
    Attributes:
        
    Methods:
        
         
    """
    
    def __init__(self, instruction: InstructionInput = None, qubits: Iterable = None, clbits: Iterable =None):
        
        self.instruction = instruction
        self.qubits = qubits
        self.clbits = clbits
        
        if isinstance(instruction,BraketInstruction):
            self.gate = Gate(instruction.operator)
        
        elif isinstance(instruction,QiskitInstruction):
            #dispense with classical bit functionality
            self.gate = Gate(instruction)
            
        elif isinstance(instruction,CirqGateInstruction):
            #instruction is a cirq operation object
            self.gate = Gate(instruction.gate)
        
    def to_cirq(self):
        
        #print(self.qubits)
        qubits = [qubit.to_cirq() for qubit in self.qubits]
        gate = self.gate.to_cirq()
        
        if gate == 'CirqMeasure':
            return cirq_measure(qubits[0],key=self.clbits[0].index)
        else:
            return gate(*qubits)
        
    def to_qiskit(self):
        
        gate = self.gate.to_qiskit()
        qubits = [qubit.to_qiskit() for qubit in self.qubits]
        clbits = [clbit.output['qiskit'] for clbit in self.clbits]
        
        if isinstance(gate, QiskitMeasurementGate):
            return gate, qubits, clbits
        else:
            return gate,qubits,clbits
    
    def to_braket(self):
        
        gate = self.gate.to_braket()
        qubits = [qubit.to_braket() for qubit in self.qubits]
        clbits = []
        
        return BraketInstruction(gate,qubits)
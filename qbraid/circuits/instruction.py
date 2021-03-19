from typing import Any, Sequence, Dict, Iterable, Union
import numpy as np


from .gate import Gate
from .qubitset import QubitSet
from .clbitset import ClbitSet

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
            
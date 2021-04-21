from typing import Any, Sequence, Dict, Iterable, Union
import abc
from abc import ABC, abstractmethod
import numpy as np

#import qBraid
from .qubit import Qubit

from .qiskit.instruction import QiskitInstructionWrapper
from .cirq.instruction import CirqInstructionWrapper
from .braket.instruction import BraketInstructionWrapper
from .qbraid.instruction import QbraidInstructionWrapper

from .moment import Moment
from .qubitset import (QiskitQubitSet, CirqQubitSet, BraketQubitSet)
from .clbitset import ClbitSet
from .clbit import Clbit
from .qbraid.gate import QbraidGateWrapper
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
            #assert np.log2(len(instruction.gate.matrix)) == len(instruction.qubits)
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
    

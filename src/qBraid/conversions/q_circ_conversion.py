# -*- coding: utf-8 -*-
# All rights reserved-2019©. 

import numpy as np
from pyquil import quil, Program, gates
from qiskit import QuantumCircuit
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.measure import Measure
from cirq import circuit
p = Program()
p.inst(H(0)) # A single instruction
p.inst(H(0), H(1)) # Multiple instructions
p.inst([H(0), H(1)]) # A list of instructions
p.inst(H(i) for i in range(4)) # A generator of instructions
p.inst(("H", 1)) # A tuple representing an instruction
p.inst("H 0") # A string representing an instruction
q = Program()
p.inst(q) # Another program



def q_circ_convert(q_circ, output_circ_type='QISKIT'):
    """Quantum circuit conversion between different packages.
    in 
    Args:
        q_circ: Program class in Pyquil
                QuantumCircuit class in Qiskit
                Circuit class in cirq
    Returns:
        quantumcircuit class in the requested package.
    """

    if isinstance(q_circ, Program):
        pyquil_circ_conversion(q_circ,output_circ_type)    

    elif isinstance(q_circ, QuantumCircuit) :
        qiskit_circ_conversion(q_circ,output_circ_type)
    
    elif isinstance(qubit_operator, QubitOperator) :
        pass
    else:
        raise TypeError('Input must be an one of the QubitOperators')


def initialize_quantum_circuit(num_qubits, num_cbits=None,output_circ_type='QISKIT'):
    if output_circ_type=='QISKIT':



def pyquil_circ_conversion(q_circ, output_circ_type='QISKIT'):
    num_qubits = len(q_circ.get_qubits())
    
    inst_list = q_circ.instructions

    if output_circ_type=='QISKIT':
        initialize_quantum_circuit(num_qubit)
    for g in inst_list:
        if g.name == 'H':



def qiskit_circ_conversion(q_circ,output_circ_type):
    num_qubits = len(q_circ.qubits)
    inst_list = q_circ._data



# def cirq_circ_conversion(q_circ,output_circ_type):



def h_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.h(qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.H(qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)
    
def x_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.x(qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.X(qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)

def y_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.y(qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.Y(qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)

def z_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.z(qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.Z(qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)

def rx_gate(theta, q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.rx(theta, qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.RX(theta, qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)

def ry_gate(theta, q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.ry(theta, qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.RY(theta, qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)

def rz_gate(theta, q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.rz(theta, qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.RZ(theta, qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)

def s_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.s(qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.S(qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)

def t_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.t(qubit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.T(qubit_index))
    elif output_circ_type=="CIRQ":
        pass #(for now)

def measure(q_circ, qubit_index, cbit_index, classical_reg, output_circ_type):
    if output_circ_type=='QISKIT':
        return q_circ.measure(qubit_index,cbit_index)
    elif output_circ_type=='PYQUIL':
        return q_circ.inst(gates.MEASURE(qubit_index,classical_reg(cbit_index)))
    elif output_circ_type=="CIRQ":
        pass #(for now)


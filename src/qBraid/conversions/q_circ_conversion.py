# -*- coding: utf-8 -*-
# All rights reserved-2019©. 

import numpy as np
from pyquil import quil, Program, gates
from pyquil.quilbase import Gate, Measurement
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.measure import Measure
from cirq import Circuit


# Things to do: Make a class with a variable: circ
# rather than updating the circ variable everytime 
# an instruction is added.


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
    
    elif isinstance(q_circ, circuit) :
        pass
    else:
        raise TypeError('Input must be an one of the QubitOperators')



def initialize_qiskit_circuit(num_qubits, c_regs=None,input_circ_type='PYQUIL'):
    if input_circ_type=='PYQUIL':
        qr = QuantumRegister(num_qubits)
        qiskit_c_regs = []
        if c_regs:
            for c_reg in c_regs:
                exec('qiskit_'+str(c_reg)+' = ClassicalRegister('+str(len(c_regs[c_reg]))+','+'"'+str(c_reg)+'"'+')')
                qiskit_c_regs.append(eval('qiskit_'+str(c_reg)))
        # print(eval('qiskit_'+str(c_reg)))
        qc = QuantumCircuit(qr,*qiskit_c_regs)
        return [qr,qiskit_c_regs,qc]
            # cr = ClassicalRegister()
    elif input_circ_type=='Cirq':
        pass


def pyquil_circ_conversion(q_circ, output_circ_type='QISKIT'):
    num_qubits = len(q_circ.get_qubits())
    classical_regs = quil.get_classical_addresses_from_program(q_circ)
    inst_list = q_circ.instructions

    if output_circ_type=='QISKIT':
        [qr, cr_list, qiskit_circ] = initialize_qiskit_circuit(num_qubits, classical_regs,'PYQUIL')
        print(cr_list)
        for operation in inst_list:
            if isinstance(operation, Gate):
                if operation.name == 'H':
                    qiskit_circ = h_gate(qiskit_circ,int(operation.qubits[0].__str__()),output_circ_type)
                elif operation.name == 'X':
                    qiskit_circ=x_gate(qiskit_circ,int(operation.qubits[0].__str__()),output_circ_type)
                elif operation.name == 'Y':
                    qiskit_circ=y_gate(qiskit_circ,int(operation.qubits[0].__str__()),output_circ_type)
                elif operation.name == 'Z':
                    qiskit_circ=z_gate(qiskit_circ,int(operation.qubits[0].__str__()),output_circ_type)
                elif operation.name == 'CNOT':
                    qiskit_circ=cnot_gate(qiskit_circ,int(operation.qubits[0].__str__()),
                                int(operation.qubits[1].__str__()),output_circ_type)
                elif operation.name == 'T':
                    qiskit_circ=t_gate(qiskit_circ,int(operation.qubits[0].__str__()),output_circ_type)
                elif operation.name == 'S':
                    qiskit_circ=s_gate(qiskit_circ,int(operation.qubits[0].__str__()),output_circ_type)
                elif operation.name == 'RX':
                    qiskit_circ=rx_gate(qiskit_circ,operation.params[0],int(operation.qubits[0].__str__()),output_circ_type)
                elif operation.name == 'RY':
                    qiskit_circ=ry_gate(qiskit_circ,operation.params[0],int(operation.qubits[0].__str__()),output_circ_type)
                elif operation.name == 'RZ':
                    qiskit_circ=rz_gate(qiskit_circ,operation.params[0],int(operation.qubits[0].__str__()),output_circ_type)
                
            elif isinstance(operation, Measurement):
                c_reg_str = operation.classical_reg.name
                classical_reg = eval('qiskit_'+c_reg_str)
                qiskit_circ=measure(qiskit_circ,operation.qubit.index, )
        return qiskit_circ
def qiskit_circ_conversion(q_circ,output_circ_type):
    num_qubits = len(q_circ.qubits)
    inst_list = q_circ._data
    


# def cirq_circ_conversion(q_circ,output_circ_type):



def h_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.h(qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.H(qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)
    
def x_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.x(qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.X(qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def y_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.y(qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.Y(qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def z_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.z(qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.Z(qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def rx_gate(q_circ,theta, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.rx(theta, qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.RX(theta, qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def ry_gate(q_circ, theta, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.ry(theta, qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.RY(theta, qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def rz_gate(q_circ, theta, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.rz(theta, qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.RZ(theta, qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def s_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.s(qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.S(qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def t_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.t(qubit_index)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.T(qubit_index))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def cnot_gate(q_circ, qubit_index_control, qubit_index_target, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.cx(qubit_index_control,qubit_index_target)
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.CNOT(qubit_index_control,qubit_index_target))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)

def measure(q_circ, qubit_index, classical_reg, cbit_index, output_circ_type):
    if output_circ_type=='QISKIT':
        q_circ.measure(qubit_index,classical_reg[cbit_index])
        return q_circ
    elif output_circ_type=='PYQUIL':
        q_circ.inst(gates.MEASURE(qubit_index,classical_reg(cbit_index)))
        return q_circ
    elif output_circ_type=="CIRQ":
        pass #(for now)


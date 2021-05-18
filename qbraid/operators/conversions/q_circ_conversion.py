# -*- coding: utf-8 -*-
# All rights reserved-2019©.

import numpy as np
from pyquil import quil, Program, gates
from pyquil.quilbase import Gate, Measurement
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit import Gate, Measure
from qiskit.circuit.measure import Measure
from cirq import Circuit


# Things to do: Make a class with a variable: circ
# rather than updating the circ variable everytime
# an instruction is added.


def q_circ_convert(q_circ, output_circ_type="QISKIT"):
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
        pyquil_circ_conversion(q_circ, output_circ_type)

    elif isinstance(q_circ, QuantumCircuit):
        qiskit_circ_conversion(q_circ, output_circ_type)

    elif isinstance(q_circ, circuit):
        pass
    else:
        raise TypeError("Input must be an one of the QubitOperators")


def initialize_qiskit_circuit(num_qubits, c_regs=None, input_circ_type="PYQUIL"):
    if input_circ_type == "PYQUIL":
        qr = QuantumRegister(num_qubits)
        qiskit_c_regs = []
        qiskit_c_regs_dict = {}
        if c_regs:
            for c_reg in c_regs:
                exec(
                    "qiskit_"
                    + str(c_reg)
                    + " = ClassicalRegister("
                    + str(len(c_regs[c_reg]))
                    + ","
                    + '"'
                    + str(c_reg)
                    + '"'
                    + ")"
                )
                qiskit_c_regs.append(eval("qiskit_" + str(c_reg)))
                qiskit_c_regs_dict[str(c_reg)] = eval("qiskit_" + str(c_reg))

        # print(eval('qiskit_'+str(c_reg)))
        qc = QuantumCircuit(qr, *qiskit_c_regs)
        return [qr, qiskit_c_regs_dict, qc]
        # cr = ClassicalRegister()
    elif input_circ_type == "Cirq":
        pass


def initialize_pyquil_circuit(c_regs=None, input_circ_type="QISKIT"):
    if input_circ_type == "QISKIT":
        p = Program()
        if c_regs:
            for c_reg in c_regs:
                name = c_reg.name
                size = c_reg.size
                p.declare(name, "BIT", size)
        return p


def pyquil_circ_conversion(q_circ, output_circ_type="QISKIT"):
    num_qubits = len(q_circ.get_qubits())
    classical_regs = quil.get_classical_addresses_from_program(q_circ)
    inst_list = q_circ.instructions

    if output_circ_type == "QISKIT":
        [qr, qiskit_c_regs_dict, qiskit_circ] = initialize_qiskit_circuit(
            num_qubits, classical_regs, "PYQUIL"
        )
        print(qiskit_c_regs_dict)
        for operation in inst_list:
            if isinstance(operation, Gate):
                if operation.name == "H":
                    qiskit_circ = h_gate(
                        qiskit_circ, int(operation.qubits[0].__str__()), output_circ_type
                    )
                elif operation.name == "X":
                    qiskit_circ = x_gate(
                        qiskit_circ, int(operation.qubits[0].__str__()), output_circ_type
                    )
                elif operation.name == "Y":
                    qiskit_circ = y_gate(
                        qiskit_circ, int(operation.qubits[0].__str__()), output_circ_type
                    )
                elif operation.name == "Z":
                    qiskit_circ = z_gate(
                        qiskit_circ, int(operation.qubits[0].__str__()), output_circ_type
                    )
                elif operation.name == "CNOT":
                    qiskit_circ = cnot_gate(
                        qiskit_circ,
                        int(operation.qubits[0].__str__()),
                        int(operation.qubits[1].__str__()),
                        output_circ_type,
                    )
                elif operation.name == "T":
                    qiskit_circ = t_gate(
                        qiskit_circ, int(operation.qubits[0].__str__()), output_circ_type
                    )
                elif operation.name == "S":
                    qiskit_circ = s_gate(
                        qiskit_circ, int(operation.qubits[0].__str__()), output_circ_type
                    )
                elif operation.name == "RX":
                    qiskit_circ = rx_gate(
                        qiskit_circ,
                        operation.params[0],
                        int(operation.qubits[0].__str__()),
                        output_circ_type,
                    )
                elif operation.name == "RY":
                    qiskit_circ = ry_gate(
                        qiskit_circ,
                        operation.params[0],
                        int(operation.qubits[0].__str__()),
                        output_circ_type,
                    )
                elif operation.name == "RZ":
                    qiskit_circ = rz_gate(
                        qiskit_circ,
                        operation.params[0],
                        int(operation.qubits[0].__str__()),
                        output_circ_type,
                    )

            elif isinstance(operation, Measurement):
                c_reg_str = operation.classical_reg.name
                qiskit_cr = qiskit_c_regs_dict[c_reg_str]
                cr_index = classical_regs[c_reg_str].index(operation.classical_reg.offset)
                qiskit_circ = measure(
                    qiskit_circ, operation.qubit.index, cr_index, output_circ_type, None, qiskit_cr
                )
        return qiskit_circ


def qiskit_circ_conversion(q_circ, output_circ_type="PYQUIL"):
    num_qubits = len(q_circ.qubits)
    q_regs = q_circ.qregs
    print(q_regs)
    q_reg_name_list = []
    q_reg_size_list = []
    for qreg in q_regs:
        q_reg_name_list.append(qreg.name)
        q_reg_size_list.append(qreg.size)

    c_regs = q_circ.cregs
    inst_list = q_circ._data

    if output_circ_type == "PYQUIL":
        pyquil_circ = initialize_pyquil_circuit(c_regs=c_regs)
        for instruction in inst_list:
            if isinstance(instruction[0], Gate):
                if isinstance(instruction[0], HGate):
                    pyquil_circ = h_gate(
                        pyquil_circ,
                        qiskit_multi_to_single_qreg(
                            q_reg_name_list,
                            q_reg_size_list,
                            instruction[1][0].register.name,
                            instruction[1][0].index,
                        ),
                        output_circ_type,
                    )
                elif isinstance(instruction[0], XGate):
                    pyquil_circ = x_gate(
                        pyquil_circ,
                        qiskit_multi_to_single_qreg(
                            q_reg_name_list,
                            q_reg_size_list,
                            instruction[1][0].register.name,
                            instruction[1][0].index,
                        ),
                        output_circ_type,
                    )
                elif isinstance(instruction[0], YGate):
                    pyquil_circ = y_gate(
                        pyquil_circ,
                        qiskit_multi_to_single_qreg(
                            q_reg_name_list,
                            q_reg_size_list,
                            instruction[1][0].register.name,
                            instruction[1][0].index,
                        ),
                        output_circ_type,
                    )
                elif isinstance(instruction[0], ZGate):
                    pyquil_circ = z_gate(
                        pyquil_circ,
                        qiskit_multi_to_single_qreg(
                            q_reg_name_list,
                            q_reg_size_list,
                            instruction[1][0].register.name,
                            instruction[1][0].index,
                        ),
                        output_circ_type,
                    )
                elif isinstance(instruction[0], SGate):
                    pyquil_circ = s_gate(
                        pyquil_circ,
                        qiskit_multi_to_single_qreg(
                            q_reg_name_list,
                            q_reg_size_list,
                            instruction[1][0].register.name,
                            instruction[1][0].index,
                        ),
                        output_circ_type,
                    )
                elif isinstance(instruction[0], TGate):
                    pyquil_circ = t_gate(
                        pyquil_circ,
                        qiskit_multi_to_single_qreg(
                            q_reg_name_list,
                            q_reg_size_list,
                            instruction[1][0].register.name,
                            instruction[1][0].index,
                        ),
                        output_circ_type,
                    )
                elif isinstance(instruction[0], RXGate):
                    theta = instruction[0].params[0]
                    qubit_index = qiskit_multi_to_single_qreg(
                        q_reg_name_list,
                        q_reg_size_list,
                        instruction[1][0].register.name,
                        instruction[1][0].index,
                    )
                    pyquil_circ = rx_gate(pyquil_circ, theta, qubit_index, output_circ_type)
                elif isinstance(instruction[0], RYGate):
                    theta = instruction[0].params[0]
                    qubit_index = qiskit_multi_to_single_qreg(
                        q_reg_name_list,
                        q_reg_size_list,
                        instruction[1][0].register.name,
                        instruction[1][0].index,
                    )
                    pyquil_circ = ry_gate(pyquil_circ, theta, qubit_index, output_circ_type)
                elif isinstance(instruction[0], RZGate):
                    theta = instruction[0].params[0]
                    qubit_index = qiskit_multi_to_single_qreg(
                        q_reg_name_list,
                        q_reg_size_list,
                        instruction[1][0].register.name,
                        instruction[1][0].index,
                    )
                    pyquil_circ = rz_gate(pyquil_circ, theta, qubit_index, output_circ_type)
                elif isinstance(instruction[0], CXGate):
                    # theta = instruction[0].params[0]
                    print("I am in CNOT")
                    print(instruction[1][0].register.name)
                    print(instruction[1][0].index)
                    print(instruction[1][1].register.name)
                    print(instruction[1][1].index)
                    qubit_index_ctrl = qiskit_multi_to_single_qreg(
                        q_reg_name_list,
                        q_reg_size_list,
                        instruction[1][0].register.name,
                        instruction[1][0].index,
                    )
                    qubit_index_target = qiskit_multi_to_single_qreg(
                        q_reg_name_list,
                        q_reg_size_list,
                        instruction[1][1].register.name,
                        instruction[1][1].index,
                    )

                    pyquil_circ = cnot_gate(
                        pyquil_circ, qubit_index_ctrl, qubit_index_target, output_circ_type
                    )

            elif isinstance(instruction[0], Measure):
                pass
        return pyquil_circ


def qiskit_multi_to_single_qreg(q_reg_name_list, q_reg_size_list, name, index):
    name_index = q_reg_name_list.index(name)
    qub_in = 0
    for i in q_reg_size_list[0:name_index]:
        qub_in += i

    qub_in += index
    return qub_in


# def cirq_circ_conversion(q_circ,output_circ_type):


def h_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.h(qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.H(qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def x_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.x(qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.X(qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def y_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.y(qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.Y(qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def z_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.z(qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.Z(qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def rx_gate(q_circ, theta, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.rx(theta, qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.RX(theta, qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def ry_gate(q_circ, theta, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.ry(theta, qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.RY(theta, qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def rz_gate(q_circ, theta, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.rz(theta, qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.RZ(theta, qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def s_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.s(qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.S(qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def t_gate(q_circ, qubit_index, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.t(qubit_index)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.T(qubit_index))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def cnot_gate(q_circ, qubit_index_control, qubit_index_target, output_circ_type):
    if output_circ_type == "QISKIT":
        q_circ.cx(qubit_index_control, qubit_index_target)
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.CNOT(qubit_index_control, qubit_index_target))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)


def measure(q_circ, qubit_index, cbit_index, output_circ_type, qubit_reg=None, classical_reg=None):
    if output_circ_type == "QISKIT":
        if qubit_reg:
            q_circ.measure(qubit_reg[qubit_index], classical_reg[cbit_index])
        else:
            q_circ.measure(qubit_index, classical_reg[cbit_index])
        return q_circ
    elif output_circ_type == "PYQUIL":
        q_circ.inst(gates.MEASURE(qubit_index, classical_reg(cbit_index)))
        return q_circ
    elif output_circ_type == "CIRQ":
        pass  # (for now)

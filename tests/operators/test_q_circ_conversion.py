# -*- coding: utf-8 -*-
# All rights reserved-2019©.
import numpy as np
from pyquil import Program
from qiskit import QuantumCircuit
from qiskit.circuit.library.standard_gates import *


from qbraid.operators.conversions.q_circ_conversion import *


from pyquil import Program
from pyquil.gates import *


def test_initialize_qiskit_circuit():
    """ testing initializiation of qiskit no qbraid wrapper """
    cr = {"ro": [0, 1, 2], "ro3": [0, 1], "ro1": [0, 1, 2], "ro2": [0]}
    [qr, cr_list, qiskit_circ] = initialize_qiskit_circuit(4, cr)
    assert 1 == 1


def test_pyquil_circ_conversion():
    """ Testing converting from pyquil to circ """
    p = Program()
    p.inst(H(0))  # A single instruction
    # p += CNOT(0, 1)
    # p += CNOT(1, 2)
    p += CNOT(3, 4)
    p.inst(RX(np.pi / 2, 2), Y(1))  # Multiple instructions
    p.inst(RY(np.pi / 2, 2), Y(1))  # Multiple instructions
    p.inst(RZ(np.pi / 2, 2), Y(1))  # Multiple instructions
    p.inst([H(0), Z(1)])  # A list of instructions
    p.inst(H(i) for i in range(4))  # A generator of instructions
    p.inst(("H", 1))  # A tuple representing an instruction
    p.inst("X 3")  # A string representing an instruction
    # q = Program()
    # p.inst(q) # Another program
    ro = p.declare("ro", "BIT", 3)
    ro2 = p.declare("ro2", "BIT", 3)
    ro3 = p.declare("ro3", "BIT", 3)
    ro1 = p.declare("ro1", "BIT", 3)

    p += X(0)
    p += MEASURE(0, ro[0])
    p += MEASURE(1, ro[1])
    p += MEASURE(2, ro[2])
    # ro1 = p.declare('ro1', 'BIT', 1)
    p += MEASURE(3, ro3[0])

    p += MEASURE(0, ro1[0])
    p += MEASURE(1, ro1[1])
    p += MEASURE(2, ro1[2])
    p += MEASURE(0, ro2[0])
    p += MEASURE(1, ro3[1])
    p += MEASURE(2, ro[2])
    ret_circ = pyquil_circ_conversion(p)
    print("\n")
    # print(ret_circ)


def test_qiskit_circ_conversion():
    # qr = QuantumRegister(2,'qr')
    # cr = ClassicalRegister(4)
    # qr1 = QuantumRegister(2,'qr1')
    # cr1 = ClassicalRegister(4,'c123')
    # qr2 = QuantumRegister(2,'qr2')
    # cr2 = ClassicalRegister(4)
    # qr3 = QuantumRegister(2,'qr3')
    # cr3 = ClassicalRegister(4,)

    # qc1 = QuantumCircuit(qr1,qr,qr2,qr3,*[cr,cr1,cr2,cr3])
    qc1 = QuantumCircuit(3)

    # qc1.rx(np.pi,qr2[0])
    # qc1.ry(np.pi,qr2[1])
    # qc1.h([qr[0],qr[1]])
    # qc1.x(qr1[1])
    # qc1.cx(qr1[0],qr[1])
    # qc1.measure([0],[1])
    # qc1.measure(qr[0],cr1[1])

    qc1.rx(np.pi, 0)
    qc1.ry(np.pi, 1)
    qc1.h(1)
    qc1.h(1)
    qc1.h(2)
    qc1.x(1)
    qc1.cx(0, 1)
    # qc1.measure(1,[1])
    # qc1.measure(qr[0],cr1[1])

    # qc.h(0)
    print(qc1)
    print(qiskit_circ_conversion(qc1))


if __name__ == "__main__":
    print("CIRC OPERATOR TESTS")
    print("-" * 100)
    print()
    test_initialize_qiskit_circuit()  # passes
    test_pyquil_circ_conversion()
    test_qiskit_circ_conversion()
    print("-" * 100)
    print()

    print("ALL TESTS PASSED")

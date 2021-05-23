# -*- coding: utf-8 -*-
# All rights reserved-2019©.
import numpy as np
from openfermion.ops import QubitOperator
from openfermion.utils import count_qubits
from qiskit.quantum_info import Pauli
from qiskit.aqua.operators import WeightedPauliOperator
from qbraid.operators.conversions.qub_op_conversion import convert



def test_of_qk():
    of_test_op_1 = QubitOperator(((0, "Z"), (1, "Z"), (2, "Z"), (3, "Z")), 1.0)
    # of_test_op_2 = QubitOperator(((0, 'I'),(1, 'I'),(2, 'I'),(3, 'I'),(4, 'I')),1.0)
    of_test_op_3 = QubitOperator(((0, "X"), (1, "Y"), (2, "Z")), 1.0)
    of_test_op_4 = QubitOperator(((0, "X"), (1, "X"), (2, "X"), (3, "X")), 1.0)
    of_test_op_5 = QubitOperator(((0, "Y"), (1, "Y"), (2, "Y"), (3, "Y")), 1.0)
    of_test_op_6 = QubitOperator.identity() + of_test_op_3
    of_test_op_7 = of_test_op_1 + of_test_op_4

    correct_u_1 = np.array([1, 1, 1, 1])
    correct_v_1 = np.array([0, 0, 0, 0])
    correct_u_2 = np.zeros(3)
    correct_v_2 = np.zeros(3)
    correct_u_3 = np.array([0, 1, 1])
    correct_v_3 = np.array([1, 1, 0])
    correct_u_4 = np.zeros(4)
    correct_v_4 = np.ones(4)
    correct_u_5 = np.ones(4)
    correct_v_5 = np.ones(4)

    correct_pauli_1 = Pauli(correct_u_1, correct_v_1)
    correct_pauli_2 = Pauli(correct_u_2, correct_v_2)
    correct_pauli_3 = Pauli(correct_u_3, correct_v_3)
    correct_pauli_4 = Pauli(correct_u_4, correct_v_4)
    correct_pauli_5 = Pauli(correct_u_5, correct_v_5)

    correct_op_1 = WeightedPauliOperator(paulis=[[1.0, correct_pauli_1]])
    correct_op_2 = WeightedPauliOperator(paulis=[[1.0, correct_pauli_2]])
    correct_op_3 = WeightedPauliOperator(paulis=[[1.0, correct_pauli_3]])
    correct_op_4 = WeightedPauliOperator(paulis=[[1.0, correct_pauli_4]])
    correct_op_5 = WeightedPauliOperator(paulis=[[1.0, correct_pauli_5]])
    correct_op_6 = correct_op_2 + correct_op_3
    correct_op_7 = correct_op_1 + correct_op_4

    # gen_qub = gen_qub_op()
    # op = convert(of_test_op_7)
    x = convert(of_test_op_1)

    assert (correct_op_1 == convert(of_test_op_1))
    assert (correct_op_3 == convert(of_test_op_3))
    assert (correct_op_4 == convert(of_test_op_4))
    assert (correct_op_5 == convert(of_test_op_5))
    assert (correct_op_6 == convert(of_test_op_6))
    assert (correct_op_7 == convert(of_test_op_7))

def test_qis_of():
    qis_u_1 = np.array([1, 1, 1, 1, 0])
    qis_v_1 = np.array([0, 0, 0, 0, 0])
    qis_u_2 = np.zeros(5)
    qis_v_2 = np.zeros(5)
    qis_u_3 = np.array([0, 1, 1, 0, 0])
    qis_v_3 = np.array([1, 1, 0, 0, 0])
    qis_u_4 = np.zeros(4)
    qis_v_4 = np.ones(4)
    qis_u_5 = np.ones(4)
    qis_v_5 = np.ones(4)

    qis_pauli_1 = Pauli(qis_u_1, qis_v_1)
    qis_pauli_2 = Pauli(qis_u_2, qis_v_2)
    qis_pauli_3 = Pauli(qis_u_3, qis_v_3)
    qis_pauli_4 = Pauli(qis_u_4, qis_v_4)
    qis_pauli_5 = Pauli(qis_u_5, qis_v_5)

    qis_test_op_1 = WeightedPauliOperator(paulis=[[1.0, qis_pauli_1]])
    qis_test_op_2 = WeightedPauliOperator(paulis=[[1.0, qis_pauli_2]])
    qis_test_op_3 = WeightedPauliOperator(paulis=[[1.0, qis_pauli_3]])
    qis_test_op_4 = WeightedPauliOperator(paulis=[[1.0, qis_pauli_4]])
    qis_test_op_5 = WeightedPauliOperator(paulis=[[1.0, qis_pauli_5]])
    qis_test_op_6 = qis_test_op_1 + qis_test_op_3
    qis_test_op_7 = qis_test_op_2 + qis_test_op_3
    correct_op_1 = QubitOperator(((0, "Z"), (1, "Z"), (2, "Z"), (3, "Z")), 1.0)
    correct_op_3 = QubitOperator(((0, "X"), (1, "Y"), (2, "Z")), 1.0)
    correct_op_4 = QubitOperator(((0, "X"), (1, "X"), (2, "X"), (3, "X")), 1.0)
    correct_op_5 = QubitOperator(((0, "Y"), (1, "Y"), (2, "Y"), (3, "Y")), 1.0)
    correct_op_6 = correct_op_1 + correct_op_3
    correct_op_7 = QubitOperator.identity() + correct_op_3
    assert (correct_op_1 == convert(qis_test_op_1, "OPENFERMION"))
    assert (correct_op_3 == convert(qis_test_op_3, "OPENFERMION"))
    assert (correct_op_4 == convert(qis_test_op_4, "OPENFERMION"))
    assert (correct_op_5 == convert(qis_test_op_5, "OPENFERMION"))
    assert (correct_op_6 == convert(qis_test_op_6, "OPENFERMION"))
    assert (correct_op_7 == convert(qis_test_op_7, "OPENFERMION"))


if __name__ == "__main__":
    print("QUB OP OPERATOR TESTS")
    print("-"*100)
    print()
    test_of_qk()  # passes
    test_qis_of() # passes
    print("-"*100)
    print()

    print("ALL TESTS PASSED")

"""
Unit tests for the qbraid unitary interface.
"""

import pytest
import cirq
import numpy as np
from itertools import chain, combinations
from braket.circuits import (
    Circuit as BraketCircuit,
    Instruction as BraketInstruction,
    gates as braket_gates,
)
from cirq import Circuit as CirqCircuit
from qiskit import QuantumCircuit as QiskitCircuit

from qbraid.interface import to_unitary


def get_subsets(nqubits):
    qubits = list(range(0, nqubits))
    combos = lambda x: combinations(qubits, x)
    all_subsets = chain(*map(combos, range(0, len(qubits)+1)))
    return list(all_subsets)[1:]

def calculate_expected(gates):
    if len(gates) == 1:
        return gates[0]
    elif len(gates) == 2:
        return np.kron(gates[1], gates[0])
    else:
        return np.kron(calculate_expected(gates[2:]), np.kron(gates[1], gates[0]))

def generate_test_data(test_gate_set, contiguous=True):
    testdata = []
    gate_set = test_gate_set.copy()
    gate_set.append(braket_gates.I)
    nqubits = len(test_gate_set)
    subsets = get_subsets(nqubits)
    for ss in subsets:
        bk_instrs = []
        np_gates = []
        for index in range(max(ss)+1):
            idx = -1 if index not in ss else index
            BKGate = gate_set[idx]
            np_gate = BKGate().to_matrix()
            if idx != -1 or contiguous:
                bk_instrs.append((BKGate, index))
            np_gates.append(np_gate)
        u_expected = calculate_expected(np_gates)
        testdata.append((bk_instrs, u_expected))
    return testdata

def unitary_test_helper(bk_instrs, u_expected):
    circuit = BraketCircuit()
    for instr in bk_instrs:
        Gate, index = instr
        circuit.add_instruction(BraketInstruction(Gate(), target=index))
    u_test = to_unitary(circuit)
    return np.allclose(u_expected, u_test)

test_gate_set = [braket_gates.X, braket_gates.Y, braket_gates.Z]
test_data_contiguous_qubits = generate_test_data(test_gate_set)
test_data_non_contiguous_qubits = generate_test_data(test_gate_set, contiguous=False)


def test_bell_circuit():
    circuit = BraketCircuit().h(0).cnot(0, 1)
    h_gate = np.sqrt(1/2) * np.array([[1, 1], [1, -1]])
    h_gate_kron = np.kron(np.eye(2), h_gate)
    cnot_gate = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])
    u_expected = np.einsum('ij,jk->ki', h_gate_kron, cnot_gate)
    u_test = to_unitary(circuit)
    assert np.allclose(u_expected, u_test)


@pytest.mark.parametrize("bk_instrs,u_expected", test_data_contiguous_qubits)
def test_continguous_qubits_unitary_calc(bk_instrs,u_expected):
    assert unitary_test_helper(bk_instrs, u_expected)


# @pytest.mark.skip(reason="https://github.com/aws/amazon-braket-sdk-python/issues/295")
@pytest.mark.parametrize("bk_instrs,u_expected", test_data_non_contiguous_qubits)
def test_non_continguous_qubits_unitary_calc(bk_instrs,u_expected):
    assert unitary_test_helper(bk_instrs, u_expected)
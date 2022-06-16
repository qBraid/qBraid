"""
Unit tests for the qbraid unitary interfacing

"""
from itertools import chain, combinations

import numpy as np
import pytest
from braket.circuits import Circuit, Instruction, gates

from qbraid.interface.calculate_unitary import to_unitary, unitary_to_little_endian
from qbraid.interface.convert_to_contiguous import convert_to_contiguous


def get_subsets(nqubits):
    """Return list of all combinations up to number nqubits"""
    qubits = list(range(0, nqubits))
    combos = lambda x: combinations(qubits, x)
    all_subsets = chain(*map(combos, range(0, len(qubits) + 1)))
    return list(all_subsets)[1:]


def calculate_expected(gates):
    """Calculated expected unitary"""
    if len(gates) == 1:
        return gates[0]
    if len(gates) == 2:
        return np.kron(gates[1], gates[0])
    return np.kron(calculate_expected(gates[2:]), np.kron(gates[1], gates[0]))


def generate_test_data(input_gate_set, contiguous=True):
    """Generate test data"""
    testdata = []
    gate_set = input_gate_set.copy()
    gate_set.append(gates.I)
    nqubits = len(input_gate_set)
    subsets = get_subsets(nqubits)
    for ss in subsets:
        bk_instrs = []
        np_gates = []
        for index in range(max(ss) + 1):
            idx = -1 if index not in ss else index
            BKGate = gate_set[idx]
            np_gate = BKGate().to_matrix()
            if idx != -1 or contiguous:
                bk_instrs.append((BKGate, index))
            np_gates.append(np_gate)
        u_expected = calculate_expected(np_gates)
        testdata.append((bk_instrs, u_expected))
    return testdata


def make_circuit(bk_instrs):
    """Constructs Braket circuit from list of instructions"""
    circuit = Circuit()
    for instr in bk_instrs:
        Gate, index = instr
        circuit.add_instruction(Instruction(Gate(), target=index))
    return convert_to_contiguous(circuit, expansion=True)


test_gate_set = [gates.X, gates.Y, gates.Z]
test_data_contiguous_qubits = generate_test_data(test_gate_set)
test_data_non_contiguous_qubits = generate_test_data(test_gate_set, contiguous=False)
test_data = test_data_contiguous_qubits + test_data_non_contiguous_qubits


@pytest.mark.parametrize("bk_instrs,u_expected", test_data)
def test_unitary_calc(bk_instrs, u_expected):
    """Test calculating unitary of circuits using both contiguous and
    non-contiguous qubit indexing."""
    circuit = make_circuit(bk_instrs)
    u_test = to_unitary(circuit)
    assert np.allclose(u_expected, u_test)


@pytest.mark.parametrize("bk_instrs,u_expected", test_data)
def test_convert_be_to_le(bk_instrs, u_expected):
    """Test converting big-endian unitary to little-endian unitary."""
    circuit = make_circuit(bk_instrs)
    u_big = circuit.to_unitary()
    u_test = unitary_to_little_endian(u_big)
    assert np.allclose(u_expected, u_test)

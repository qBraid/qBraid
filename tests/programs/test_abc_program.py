# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for equivalence of interfacing quantum programs

"""
import numpy as np
import pytest
from braket.circuits import Circuit as BKCircuit
from cirq import Circuit, LineQubit, X, Y, Z

from qbraid import circuit_wrapper
from qbraid.interface.random.random import random_circuit, random_unitary_matrix
from qbraid.programs.testing.circuit_equality import circuits_allclose

from ..fixtures.programs import bell_data, shared15_data

bell_map, _ = bell_data()
braket_bell = bell_map["braket"]()
cirq_bell = bell_map["cirq"]()
pyquil_bell = bell_map["pyquil"]()
qiskit_bell = bell_map["qiskit"]()
pytket_bell = bell_map["pytket"]()
qasm2_bell = bell_map["qasm2"]()
qasm3_bell = bell_map["qasm3"]()

shared15_map, _ = shared15_data()
braket_shared15 = shared15_map["braket"]()
cirq_shared15 = shared15_map["cirq"]()
pyquil_shared15 = shared15_map["pyquil"]()
qiskit_shared15 = shared15_map["qiskit"]()
pytket_shared15 = shared15_map["pytket"]()
qasm2_shared15 = shared15_map["qasm2"]()
qasm3_shared15 = shared15_map["qasm3"]()


def test_bell():
    """Test the equality of bell circuits"""

    eq1 = circuits_allclose(braket_bell, cirq_bell, strict_gphase=True)
    eq2 = circuits_allclose(cirq_bell, pyquil_bell, strict_gphase=True)
    eq3 = circuits_allclose(pyquil_bell, qiskit_bell, strict_gphase=True)
    eq4 = circuits_allclose(qiskit_bell, pytket_bell, strict_gphase=True)
    eq5 = circuits_allclose(pytket_bell, qasm2_bell, strict_gphase=True)
    eq6 = circuits_allclose(qasm2_bell, qasm3_bell, strict_gphase=True)

    assert eq1 and eq2 and eq3 and eq4 and eq5 and eq6


def test_shared15():
    """Test the equality of shared gates circuits"""

    eq1 = circuits_allclose(braket_shared15, cirq_shared15, strict_gphase=True)
    eq2 = circuits_allclose(cirq_shared15, pyquil_shared15, strict_gphase=False)
    eq3 = circuits_allclose(pyquil_shared15, qiskit_shared15, strict_gphase=False)
    eq4 = circuits_allclose(qiskit_shared15, pytket_shared15, strict_gphase=True)
    eq5 = circuits_allclose(pytket_shared15, qasm2_shared15, strict_gphase=True)
    eq6 = circuits_allclose(qasm2_shared15, qasm3_shared15, strict_gphase=False)

    assert eq1 and eq2 and eq3 and eq4 and eq5 and eq6


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit"])
def test_random(package):
    """Test generating random circuits"""
    try:
        random_circuit(package)
    except Exception:  # pylint: disable=broad-exception-caught
        assert False
    assert True


def test_collapse_empty_braket_cirq():
    """Test unitary equivalance after converting to contiguous qubits"""
    # pylint: disable=no-member
    braket_circuit = BKCircuit()
    braket_circuit.x(0)
    braket_circuit.y(2)
    braket_circuit.z(4)
    # pylint: enable=no-member
    assert braket_circuit.qubit_count == 3

    cirq_circuit = Circuit()
    q0 = LineQubit(0)
    q2 = LineQubit(2)
    q4 = LineQubit(4)
    cirq_circuit.append(X(q0))
    cirq_circuit.append(Y(q2))
    cirq_circuit.append(Z(q4))
    assert len(cirq_circuit.all_qubits()) == 3

    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)

    qprogram = circuit_wrapper(braket_circuit)
    qprogram.remove_idle_qubits()
    braket_compat_circuit = qprogram.program
    assert braket_compat_circuit.qubit_count == 3

    qprogram = circuit_wrapper(cirq_circuit)
    qprogram.remove_idle_qubits()
    cirq_compat_circuit = qprogram.program
    assert circuits_allclose(braket_compat_circuit, cirq_compat_circuit, strict_gphase=True)

    qprogram = circuit_wrapper(cirq_circuit)
    qprogram.populate_idle_qubits()
    cirq_expanded_circuit = qprogram.program
    assert len(cirq_expanded_circuit.all_qubits()) == 5


def test_random_unitary():
    """Test generating random unitary"""
    matrix = random_unitary_matrix(2)
    assert np.allclose(matrix @ matrix.conj().T, np.eye(2))

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
from qbraid.inspector import get_program_type
from qbraid.interface.circuit_equality import circuits_allclose
from qbraid.interface.random.random import random_circuit, random_unitary_matrix

from ..fixtures import packages_bell, packages_shared15


def pair_packages(packages):
    """Return a list of tuples of packages to compare"""
    return [(packages[i], packages[i + 1]) for i in range(len(packages) - 1)]


bell_pairs = pair_packages(packages_bell)
shared15_pairs = pair_packages(packages_shared15)


@pytest.mark.parametrize("two_bell_circuits", bell_pairs, indirect=True)
def test_compare_bell_circuits(two_bell_circuits):
    """Test unitary equivalance of bell circuits across packages for
    testing baseline."""
    circuit1, circuit2, _, _ = two_bell_circuits
    assert circuits_allclose(circuit1, circuit2, strict_gphase=True)


@pytest.mark.parametrize("two_shared15_circuits", shared15_pairs, indirect=True)
def test_compare_shared15_circuits(two_shared15_circuits):
    """Test unitary equivalance of shared15 circuits across packages for
    testing baseline."""
    circuit1, circuit2, package1, package2 = two_shared15_circuits
    strict_gphase = not (
        "pyquil" in {package1, package2} or {package1, package2} == {"qasm2", "qasm3"}
    )
    assert circuits_allclose(circuit1, circuit2, strict_gphase=strict_gphase)


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit"])
def test_random(package):
    """Test generating random circuits"""
    program = random_circuit(package)
    assert get_program_type(program) == package


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

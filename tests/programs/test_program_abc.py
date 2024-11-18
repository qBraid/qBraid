# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for equivalence of interfacing quantum programs

"""
from __future__ import annotations

from unittest.mock import Mock

import numpy as np
import pytest
from braket.circuits import Circuit as BKCircuit
from cirq import Circuit, LineQubit, X, Y, Z

from qbraid.interface.circuit_equality import circuits_allclose
from qbraid.interface.random.random import random_circuit, random_unitary_matrix
from qbraid.programs import get_program_type_alias, load_program
from qbraid.programs.ahs import AnalogHamiltonianProgram
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model import GateModelProgram

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
    try:
        equal = circuits_allclose(circuit1, circuit2)
        assert equal
    except NotImplementedError:
        pytest.skip("Not implemented")


@pytest.mark.parametrize("two_shared15_circuits", shared15_pairs, indirect=True)
def test_compare_shared15_circuits(two_shared15_circuits):
    """Test unitary equivalance of shared15 circuits across packages for
    testing baseline."""
    circuit1, circuit2, package1, package2 = two_shared15_circuits
    strict_gphase = not (
        "pyquil" in {package1, package2}
        or {package1, package2} == {"qasm2", "qasm3"}
        or {package1, package2} == {"pytket", "qasm2"}
    )
    try:
        equal = circuits_allclose(circuit1, circuit2, strict_gphase=strict_gphase)
        assert equal
    except NotImplementedError:
        pytest.skip("Not implemented")


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit"])
def test_random(package):
    """Test generating random circuits"""
    program = random_circuit(package)
    assert get_program_type_alias(program) == package


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

    qprogram = load_program(braket_circuit)
    qprogram.remove_idle_qubits()
    braket_compat_circuit = qprogram.program
    assert braket_compat_circuit.qubit_count == 3

    qprogram = load_program(cirq_circuit)
    qprogram.remove_idle_qubits()
    cirq_compat_circuit = qprogram.program
    assert circuits_allclose(braket_compat_circuit, cirq_compat_circuit, strict_gphase=True)

    qprogram = load_program(cirq_circuit)
    qprogram.populate_idle_qubits()
    cirq_expanded_circuit = qprogram.program
    assert len(cirq_expanded_circuit.all_qubits()) == 5


def test_random_unitary():
    """Test generating random unitary"""
    matrix = random_unitary_matrix(2)
    assert np.allclose(matrix @ matrix.conj().T, np.eye(2))


class FakeProgram(GateModelProgram):
    """Fake program for testing"""

    def __init__(self):
        super().__init__("OPENQASM 2.0;qreg q[2];h q[0];cx q[0],q[1];")

    @property
    def qubits(self):
        raise NotImplementedError

    @property
    def num_clbits(self):
        """Return the number of classical bits in the circuit."""
        raise NotImplementedError

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        raise NotImplementedError

    def _unitary(self) -> np.ndarray:
        """Calculate unitary of circuit."""
        raise NotImplementedError

    def remove_idle_qubits(self):
        """Remove empty registers of circuit."""
        raise NotImplementedError

    def reverse_qubit_order(self):
        """Rerverse qubit ordering of circuit."""
        raise NotImplementedError


@pytest.fixture
def fake_program():
    """Return a FakeProgram object."""
    return FakeProgram()


@pytest.mark.parametrize(
    "matrix",
    [
        np.array([[1, 2, 3], [4, 5, 6]]),  # Non-square matrix
        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),  # Square but not a power of 2
    ],
)
def test_unitary_rev_qubits_value_errors(matrix, fake_program):
    """Test that unitary_rev_qubits raises a ValueError for invalid input matrices."""
    expected_error_msg = "Input matrix must be a square matrix of size 2^N for some integer N."
    with pytest.raises(ValueError) as excinfo:
        fake_program._unitary = lambda: matrix
        fake_program.unitary_rev_qubits()
    assert expected_error_msg in str(excinfo.value)


@pytest.mark.parametrize(
    "matrix",
    [
        np.array([[1, 2], [3, 4]]),  # Not a unitary matrix, simple 2x2 case
        np.array([[0, 1], [1, 0], [0, 0]]),  # Non-square matrix which cannot be unitary
    ],
)
def test_unitary_little_endian_non_unitary_matrix_raises_value_error(matrix, fake_program):
    """Test that unitary_little_endian raises a ValueError for non-unitary matrices."""
    expected_error_msg = "Input matrix must be unitary."
    with pytest.raises(ValueError) as excinfo:
        fake_program.unitary = lambda: matrix
        fake_program.unitary_little_endian()
    assert expected_error_msg in str(excinfo.value)


def test_program_type_error():
    """Test error setting different type of same program"""
    braket_circuit = BKCircuit()
    braket_circuit.x(0)
    braket_circuit.y(2)
    braket_circuit.z(4)

    qbraid_circuit = load_program(braket_circuit)
    with pytest.raises(ProgramTypeError):
        qbraid_circuit.program = "string"


def test_ahs_program_transform():
    """Test that AHS transform method does not modify the program."""

    class MyAHS(AnalogHamiltonianProgram):
        """Fake AnalogHamiltonianProgram for testing."""

        def to_dict(self):
            """Mock to_dict method."""
            return self.program

    ahs_json = {"hamiltonian": {"terms": []}, "register": {"sites": [], "filling": []}}
    program = MyAHS(ahs_json)
    program.transform(device=Mock())
    assert program.program == ahs_json

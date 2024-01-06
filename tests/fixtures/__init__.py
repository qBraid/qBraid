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
Module containing fixtures for testing

"""
import pytest

from .braket.circuits import braket_bell, braket_shared15
from .cirq.circuits import cirq_bell, cirq_shared15
from .pennylane.circuits import pennylane_bell, pennylane_shared15
from .pyquil.circuits import pyquil_bell, pyquil_shared15
from .pytket.circuits import pytket_bell, pytket_shared15
from .qasm2.circuits import qasm2_bell, qasm2_cirq_shared15
from .qasm3.circuits import qasm3_bell, qasm3_shared15
from .qiskit.circuits import qiskit_bell, qiskit_shared15

# Map package names to their bell circuit functions
bell_circuit_functions = {
    "braket": braket_bell,
    "pennylane": pennylane_bell,
    "cirq": cirq_bell,
    "pyquil": pyquil_bell,
    "qiskit": qiskit_bell,
    "pytket": pytket_bell,
    "qasm2": qasm2_bell,
    "qasm3": qasm3_bell,
}

# Map package names to their shared15 circuit functions
shared15_circuit_functions = {
    "braket": braket_shared15,
    "pennylane": pennylane_shared15,
    "cirq": cirq_shared15,
    "pyquil": pyquil_shared15,
    "qiskit": qiskit_shared15,
    "pytket": pytket_shared15,
    "qasm2": qasm2_cirq_shared15,
    "qasm3": qasm3_shared15,
}


@pytest.fixture
def bell_circuit(request):
    """Fixture for getting bell circuit for a given package."""
    package = request.param
    circuit_func = bell_circuit_functions[package]
    circuit = circuit_func()
    return circuit, package


@pytest.fixture
def two_bell_circuits(request):
    """Fixture for getting two bell circuits from two different packages."""
    package1, package2 = request.param
    circuit1 = bell_circuit_functions[package1]()
    circuit2 = bell_circuit_functions[package2]()
    return circuit1, circuit2, package1, package2


@pytest.fixture
def bell_unitary():
    """Fixture containing unitary for bell circuit."""
    circuit = cirq_bell()
    return circuit.unitary()


@pytest.fixture
def shared15_circuit(request):
    """Fixture for getting shared15 circuit and unitary for a specific package."""
    package = request.param
    circuit_func = shared15_circuit_functions[package]
    circuit = circuit_func()
    return circuit, package


@pytest.fixture
def two_shared15_circuits(request):
    """Fixture for getting two shared15 circuits from two different packages."""
    package1, package2 = request.param
    circuit1 = shared15_circuit_functions[package1]()
    circuit2 = shared15_circuit_functions[package2]()
    return circuit1, circuit2, package1, package2


@pytest.fixture
def shared15_unitary():
    """Fixture containing unitary for shared15 circuit."""
    circuit = cirq_shared15()
    return circuit.unitary()


packages_bell = list(bell_circuit_functions.keys())
packages_shared15 = list(shared15_circuit_functions.keys())

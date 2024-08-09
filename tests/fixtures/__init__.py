# Copyright (C) 2024 qBraid
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
import importlib.util

import numpy as np
import pytest

from qbraid.programs import load_program


def import_circuit_functions(module_name, bell_func_name, shared15_func_name):
    """Attempt to import bell and shared15 functions from a given module."""
    # Construct the full module path assuming the current module is the root
    package = f".{module_name}.circuits"
    try:
        # Attempt to import the module relatively to the current script
        circuits = importlib.import_module(package, __package__)
    except ImportError:
        return None, None  # The module is not installed

    # Get the bell and shared15 functions
    bell_func = getattr(circuits, bell_func_name, None)
    shared15_func = getattr(circuits, shared15_func_name, None)
    return bell_func, shared15_func


# Define the modules and their respective function names
modules_info = {
    "braket": ("braket_bell", "braket_shared15"),
    "pennylane": ("pennylane_bell", "pennylane_shared15"),
    "cirq": ("cirq_bell", "cirq_shared15"),
    "pyquil": ("pyquil_bell", "pyquil_shared15"),
    "qiskit": ("qiskit_bell", "qiskit_shared15"),
    "pytket": ("pytket_bell", "pytket_shared15"),
    "qasm2": ("qasm2_bell", "qasm2_cirq_shared15"),
    "qasm3": ("qasm3_bell", "qasm3_shared15"),
}

bell_circuit_functions = {}
shared15_circuit_functions = {}

# Attempt to import each module and retrieve the bell and shared15 functions
for module, (bell_function_name, shared15_function_name) in modules_info.items():
    bell_function, shared15_function = import_circuit_functions(
        module, bell_function_name, shared15_function_name
    )
    if bell_function:
        bell_circuit_functions[module] = bell_function
    if shared15_function:
        shared15_circuit_functions[module] = shared15_function


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
    try:
        circuit1 = bell_circuit_functions[package1]()
    except KeyError:
        circuit1 = None
    try:
        circuit2 = bell_circuit_functions[package2]()
    except KeyError:
        circuit2 = None

    return circuit1, circuit2, package1, package2


@pytest.fixture
def bell_unitary():
    """Fixture containing unitary for bell circuit."""
    return np.array(
        [
            [0.70710678 + 0.0j, 0.0 + 0.0j, 0.70710678 + 0.0j, 0.0 + 0.0j],
            [0.0 + 0.0j, 0.70710678 + 0.0j, 0.0 + 0.0j, 0.70710678 + 0.0j],
            [0.0 + 0.0j, 0.70710678 + 0.0j, 0.0 + 0.0j, -0.70710678 + 0.0j],
            [0.70710678 + 0.0j, 0.0 + 0.0j, -0.70710678 + 0.0j, 0.0 + 0.0j],
        ]
    )


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
    if "cirq" in shared15_circuit_functions:
        circuit = shared15_circuit_functions["cirq"]()
    elif "qiskit" in shared15_circuit_functions:
        circuit = shared15_circuit_functions["qiskit"]()
    elif "braket" in shared15_circuit_functions:
        circuit = shared15_circuit_functions["braket"]()
    elif "pennylane" in shared15_circuit_functions:
        circuit = shared15_circuit_functions["pennylane"]()
    elif "pyquil" in shared15_circuit_functions:
        circuit = shared15_circuit_functions["pyquil"]()
    elif "pytket" in shared15_circuit_functions:
        circuit = shared15_circuit_functions["pytket"]()
    else:
        raise ValueError("No shared15 baseline circuit found")

    program = load_program(circuit)
    return program.unitary()


packages_bell = list(bell_circuit_functions.keys())
packages_shared15 = list(shared15_circuit_functions.keys())

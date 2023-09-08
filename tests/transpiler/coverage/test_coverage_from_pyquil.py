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
Benchmarking tests for pyQuil conversions

"""
import string

import numpy as np
import pyquil
import pytest

import qbraid


def generate_params(varnames, seed=0):
    """Generate random parameters to help construct PyQuil test gates"""
    np.random.seed(seed)
    params = {}
    rot_args = ["angle", "phi", "lam", "gamma"]
    for ra in rot_args:
        if ra in varnames:
            params[ra] = np.random.rand() * 2 * np.pi

    if "qubit" in varnames:
        params["qubit"] = 0

    if "control" in varnames:
        params["control"] = 0
        params["target"] = 1

    if "q1" in varnames:
        params["q1"] = 0
        params["q2"] = 1

    return params


def get_pyquil_gates():
    """Construct a dictionary of all pyQuil gates and assign random parameters as applicable"""
    pyquil_gate_dict = {
        attr: None for attr in dir(pyquil.gates) if attr[0] in string.ascii_uppercase
    }

    for gate in pyquil_gate_dict:
        try:
            params = generate_params(getattr(pyquil.gates, gate).__code__.co_varnames)
            pyquil_gate_dict[gate] = getattr(pyquil.gates, gate)(**params)
        except Exception:  # pylint: disable=broad-exception-caught
            continue

    return {k: v for k, v in pyquil_gate_dict.items() if v is not None}


#############
### TESTS ###
#############

TARGETS = [("braket", 0.77), ("cirq", 0.77), ("pytket", 0.77), ("qiskit", 0.77)]
pyquil_gates = get_pyquil_gates()


def convert_from_pyquil_to_x(target, gate_name):
    """Construct a pyQuil programs with the given gate, transpile it to
    target program type, and check equivalence.
    """
    gate = pyquil_gates[gate_name]
    source_circuit = pyquil.Program()
    source_circuit += gate
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), TARGETS)
def test_pyquil_coverage(target, baseline):
    """Test converting pyQuil programs to supported target program type over
    all pyQuil gates and check against baseline expecte accuracy.
    """
    ACCURACY_BASELINE = baseline
    ALLOWANCE = 0.01
    failures = {}
    for gate_name in pyquil_gates:
        try:
            convert_from_pyquil_to_x(target, gate_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            failures[f"{target}-{gate_name}"] = e

    total_tests = len(pyquil_gates)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails
    accuracy = float(nb_passes) / float(total_tests)

    assert accuracy >= ACCURACY_BASELINE - ALLOWANCE, (
        f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed "
        f"({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed "
        f"(expected >= {ACCURACY_BASELINE}).\nFailures: {failures.keys()}\n\n"
    )

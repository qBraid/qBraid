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
Benchmarking tests for braket conversions

"""
import string

import braket
import numpy as np
import pytest
import scipy

import qbraid


def generate_params(varnames):
    params = {}
    for v in varnames:
        if v.startswith("angle"):
            params[v] = np.random.rand() * 2 * np.pi
    return params


def get_braket_gates():
    braket_gates = {
        attr: None for attr in dir(braket.circuits.Gate) if attr[0] in string.ascii_uppercase
    }

    for gate in ["C", "PulseGate"]:
        braket_gates.pop(gate)

    for gate in braket_gates:
        if gate == "Unitary":
            n = np.random.randint(1, 4)
            unitary = scipy.stats.unitary_group.rvs(2**n)
            braket_gates[gate] = getattr(braket.circuits.Gate, gate)(matrix=unitary)
        else:
            params = generate_params(
                getattr(braket.circuits.Gate, gate).__init__.__code__.co_varnames
            )
            braket_gates[gate] = getattr(braket.circuits.Gate, gate)(**params)
    return {k: v for k, v in braket_gates.items() if v is not None}


#############
### TESTS ###
#############

TARGETS = [("cirq", 1.0), ("pyquil", 1.0), ("pytket", 1.0), ("qiskit", 1.0)]
braket_gates = get_braket_gates()


def convert_from_braket_to_x(target, gate_name):
    gate = braket_gates[gate_name]

    if gate.qubit_count == 1:
        source_circuit = braket.circuits.Circuit([braket.circuits.Instruction(gate, 0)])
    else:
        source_circuit = braket.circuits.Circuit(
            [braket.circuits.Instruction(gate, range(gate.qubit_count))]
        )

    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), TARGETS)
def test_braket_coverage(target, baseline):
    ACCURACY_BASELINE = baseline
    ALLOWANCE = 0.01
    failures = {}
    for gate_name in braket_gates:
        try:
            convert_from_braket_to_x(target, gate_name)
        except Exception as e:
            failures[f"{target}-{gate_name}"] = e

    total_tests = len(braket_gates)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails
    accuracy = float(nb_passes) / float(total_tests)

    assert (
        nb_passes >= ACCURACY_BASELINE - ALLOWANCE
    ), f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed ({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed (expected >= {ACCURACY_BASELINE}).\nFailures: {failures.keys()}\n\n"

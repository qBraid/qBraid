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
Benchmarking tests for cirq conversions

"""
import string

import cirq
import numpy as np
import scipy

import qbraid

#############
### BASE ####
#############

CIRQ_BASELINE = 205
ALLOWANCE = 2

#############
### UTILS ###
#############


def generate_params(varnames):
    params = {}
    # Generating angles
    for ra in ["rads", "theta", "phi"]:
        if ra in varnames:
            params[ra] = np.random.rand() * 2 * np.pi
    # Generating probabilities
    for prob in ["gamma", "p", "probability"]:
        if prob in varnames:
            params[prob] = np.random.rand()

    # exponents
    for exp in ["exponent", "x_exponent", "z_exponent", "phase_exponent", "axis_phase_exponent"]:
        if exp in varnames:
            params[exp] = np.random.rand() * 10

    if "num_qubits" in varnames:
        params["num_qubits"] = np.random.randint(1, 7)

    if "sub_gate" in varnames:
        params["sub_gate"] = np.random.choice([cirq.X, cirq.Y, cirq.Z, cirq.S, cirq.T])

    if "matrix" in varnames:
        n = np.random.randint(1, 4)
        params["matrix"] = scipy.stats.unitary_group.rvs(2**n)

    return params


def get_cirq_gates():
    qubits = cirq.LineQubit.range(7)

    cirq_gates = {
        attr: None
        for attr in dir(cirq.ops)
        if attr[0] in string.ascii_uppercase
        if (
            isinstance(getattr(cirq.ops, attr), cirq.value.abc_alt.ABCMetaImplementAnyOneOf)
            or isinstance(getattr(cirq.ops, attr), cirq.Gate)
        )
    }
    for gate in cirq_gates:
        try:
            params = generate_params(getattr(cirq.ops, gate).__init__.__code__.co_varnames)
        except:
            continue

        if not isinstance(getattr(cirq.ops, gate), cirq.Gate):
            try:
                cirq_gates[gate] = getattr(cirq.ops, gate)(**params)
            except Exception as e:
                continue

    for gate in cirq_gates:
        if cirq_gates.get(gate):
            cirq_gates[gate] = cirq_gates[gate](*qubits[: cirq_gates[gate].num_qubits()])
        else:
            try:
                cirq_gates[gate] = getattr(cirq.ops, gate)(
                    *qubits[: getattr(cirq.ops, gate).num_qubits()]
                )
            except Exception as e:
                continue

    return {k: v for k, v in cirq_gates.items() if v is not None}


#############
### TESTS ###
#############

TARGETS = ["braket", "pyquil", "pytket", "qiskit"]
cirq_gates = get_cirq_gates()
paramslist = [(target, gate) for target in TARGETS for gate in cirq_gates]
failures = {}


def convert_from_cirq_to_x(target, gate_name):
    gate = cirq_gates[gate_name]
    source_circuit = cirq.Circuit()
    source_circuit.append(gate)
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


def test_cirq_coverage():
    for target in TARGETS:
        for gate_name in cirq_gates:
            try:
                convert_from_cirq_to_x(target, gate_name)
            except Exception as e:
                failures[f"{target}-{gate_name}"] = e

    total_tests = len(cirq_gates) * len(TARGETS)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails

    print(
        f"A total of {len(cirq_gates)} gates were tested (for a total of {total_tests} tests). {nb_fails}/{total_tests} tests failed ({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed."
    )
    print("Failures:", failures.keys())

    assert (
        nb_passes >= CIRQ_BASELINE - ALLOWANCE
    ), f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed ({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed (expected >= {CIRQ_BASELINE}).\nFailures: {failures.keys()}\n\n"

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
Benchmarking tests for Cirq conversions

"""
import importlib.util
import string

import cirq
import numpy as np
import pytest
import scipy

from qbraid.interface import circuits_allclose
from qbraid.transpiler import ConversionGraph, transpile


def generate_params(varnames, seed=0):
    """Generate random parameters to help construct Cirq test gates"""
    np.random.seed(seed)
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
    """Construct a dictionary of all Cirq gates and assign random parameters as applicable"""
    qubits = cirq.LineQubit.range(7)

    cirq_gate_dict = {
        attr: None
        for attr in dir(cirq.ops)
        if attr[0] in string.ascii_uppercase
        if (
            isinstance(
                getattr(cirq.ops, attr), (cirq.Gate, cirq.value.abc_alt.ABCMetaImplementAnyOneOf)
            )
        )
    }
    for gate in cirq_gate_dict:
        try:
            params = generate_params(getattr(cirq.ops, gate).__init__.__code__.co_varnames)
        except Exception:  # pylint: disable=broad-exception-caught
            continue

        if not isinstance(getattr(cirq.ops, gate), cirq.Gate):
            try:
                cirq_gate_dict[gate] = getattr(cirq.ops, gate)(**params)
            except Exception:  # pylint: disable=broad-exception-caught
                continue

    for gate in cirq_gate_dict:
        if cirq_gate_dict.get(gate):
            cirq_gate_dict[gate] = cirq_gate_dict[gate](
                *qubits[: cirq_gate_dict[gate].num_qubits()]
            )
        else:
            try:
                cirq_gate_dict[gate] = getattr(cirq.ops, gate)(
                    *qubits[: getattr(cirq.ops, gate).num_qubits()]
                )
            except Exception:  # pylint: disable=broad-exception-caught
                continue

    return {k: v for k, v in cirq_gate_dict.items() if v is not None}


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


ALL_TARGETS = [("braket", 0.85), ("pyquil", 0.74), ("pytket", 0.87), ("qiskit", 0.87)]
AVAILABLE_TARGETS = [(name, version) for name, version in ALL_TARGETS if is_package_installed(name)]

cirq_gates = get_cirq_gates()

graph = ConversionGraph(require_native=True)


def convert_from_cirq_to_x(target, gate_name):
    """Construct a Cirq circuit with the given gate, transpile it to
    target program type, and check equivalence.
    """
    gate = cirq_gates[gate_name]
    source_circuit = cirq.Circuit()
    source_circuit.append(gate)
    target_circuit = transpile(source_circuit, target, conversion_graph=graph)
    assert circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), AVAILABLE_TARGETS)
def test_cirq_coverage(target, baseline):
    """Test converting Cirq circuits to supported target program type over
    all Cirq gates and check against baseline expecte accuracy.
    """
    ACCURACY_BASELINE = baseline
    ALLOWANCE = 0.01
    failures = {}
    for gate_name in cirq_gates:
        try:
            convert_from_cirq_to_x(target, gate_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            failures[f"{target}-{gate_name}"] = e

    total_tests = len(cirq_gates)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails
    accuracy = float(nb_passes) / float(total_tests)

    assert accuracy >= ACCURACY_BASELINE - ALLOWANCE, (
        f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed "
        f"({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed "
        f"(expected >= {ACCURACY_BASELINE}).\nFailures: {failures.keys()}\n\n"
    )

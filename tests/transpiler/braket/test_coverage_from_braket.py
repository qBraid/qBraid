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
Benchmarking tests for Amazon Braket conversions

"""
import importlib.util

import braket.circuits
import pytest

from qbraid.interface import circuits_allclose
from qbraid.transpiler import ConversionGraph, transpile

from ...fixtures.braket.gates import get_braket_gates


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


ALL_TARGETS = [("cirq", 1.0), ("pyquil", 0.84), ("pytket", 1.0), ("qiskit", 1.0)]
AVAILABLE_TARGETS = [(name, version) for name, version in ALL_TARGETS if is_package_installed(name)]

braket_gates = get_braket_gates(seed=0)

graph = ConversionGraph(require_native=True)

# TODO: Update Pyqasm with the definitions / fix errors of these gates
GATES_TO_SKIP = {"MS"}


def convert_from_braket_to_x(target, gate_name):
    """Construct an Amazon Braket circuit with the given gate, transpile it to
    target program type, and check equivalence.
    """
    gate = braket_gates[gate_name]

    if gate.qubit_count == 1:
        source_circuit = braket.circuits.Circuit([braket.circuits.Instruction(gate, 0)])
    else:
        source_circuit = braket.circuits.Circuit(
            [braket.circuits.Instruction(gate, range(gate.qubit_count))]
        )
    target_circuit = transpile(source_circuit, target, conversion_graph=graph)
    assert circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), AVAILABLE_TARGETS)
def test_braket_coverage(target, baseline):
    """Test converting Amazon Braket circuits to supported target program type over
    all Amazon Braket gates and check against baseline expecte accuracy.
    """
    ACCURACY_BASELINE = baseline
    ALLOWANCE = 0.01
    failures = {}
    for gate_name in braket_gates:
        if gate_name in GATES_TO_SKIP:
            continue
        try:
            convert_from_braket_to_x(target, gate_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            failures[f"{target}-{gate_name}"] = e

    total_tests = len(braket_gates) - len(GATES_TO_SKIP)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails
    accuracy = float(nb_passes) / float(total_tests)

    assert accuracy >= ACCURACY_BASELINE - ALLOWANCE, (
        f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed "
        f"({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed "
        f"(expected >= {ACCURACY_BASELINE}).\nFailures: {failures.keys()}\n\n"
    )

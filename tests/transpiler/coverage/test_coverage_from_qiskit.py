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
Benchmarking tests for Qiskit conversions

"""
import pytest
import qiskit

import qbraid

from ..._data.qiskit.gates import get_qiskit_gates

TARGETS = [("braket", 0.98), ("cirq", 0.98), ("pyquil", 0.81), ("pytket", 0.98)]
qiskit_gates = get_qiskit_gates(seed=0)


def convert_from_qiskit_to_x(target, gate_name):
    """Construct a Qiskit circuit with the given gate, transpile it to
    target program type, and check equivalence.
    """
    gate = qiskit_gates[gate_name]
    source_circuit = qiskit.QuantumCircuit(gate.num_qubits)
    source_circuit.compose(gate, inplace=True)
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), TARGETS)
def test_qiskit_coverage(target, baseline):
    """Test converting Qiskit circuits to supported target program type over
    all Qiskit standard gates and check against baseline expecte accuracy.
    """
    ACCURACY_BASELINE = baseline
    ALLOWANCE = 0.01
    failures = {}
    for gate_name in qiskit_gates:
        try:
            convert_from_qiskit_to_x(target, gate_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            failures[f"{target}-{gate_name}"] = e

    total_tests = len(qiskit_gates)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails
    accuracy = float(nb_passes) / float(total_tests)

    assert accuracy >= ACCURACY_BASELINE - ALLOWANCE, (
        f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed "
        f"({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed "
        f"(expected >= {ACCURACY_BASELINE}).\nFailures: {failures.keys()}\n\n"
    )

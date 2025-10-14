# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Benchmarking tests for Qiskit conversions

"""
import importlib.util

import pytest
import qiskit

from qbraid.interface import circuits_allclose
from qbraid.transpiler import ConversionGraph, transpile

from ...fixtures.qiskit.gates import get_qiskit_gates


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


ALL_TARGETS = [("braket", 1.0), ("cirq", 1.0), ("pyquil", 0.98), ("pytket", 1.0)]
AVAILABLE_TARGETS = [(name, version) for name, version in ALL_TARGETS if is_package_installed(name)]

qiskit_gates = get_qiskit_gates(seed=0, exclude=["GlobalPhaseGate"])

graph = ConversionGraph(require_native=True)


def convert_from_qiskit_to_x(target, gate_name):
    """Construct a Qiskit circuit with the given gate, transpile it to
    target program type, and check equivalence.
    """
    gate = qiskit_gates[gate_name]
    source_circuit = qiskit.QuantumCircuit(gate.num_qubits)
    source_circuit.compose(gate, inplace=True)
    target_circuit = transpile(source_circuit, target, conversion_graph=graph)
    assert circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), AVAILABLE_TARGETS)
def test_qiskit_coverage(target, baseline):
    """Test converting Qiskit circuits to supported target program type over
    all Qiskit standard gates and check against baseline expected accuracy.
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

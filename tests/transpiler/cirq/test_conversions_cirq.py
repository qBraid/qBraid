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
Unit tests for the qbraid transpiler conversions module.

"""
from typing import Optional

import cirq
import numpy as np
import pytest

from qbraid.interface.circuit_equality import circuits_allclose
from qbraid.programs import NATIVE_REGISTRY, load_program
from qbraid.transpiler.conversions import conversion_functions
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.graph import ConversionGraph


def find_cirq_targets(skip: Optional[list[str]] = None):
    """Find all Cirq conversion targets."""
    skip = skip or []
    cirq_targets = []
    for function in conversion_functions:
        if function.startswith("cirq_to_"):
            _, target_library = function.split("_to_")
            if target_library not in skip and target_library in NATIVE_REGISTRY:
                cirq_targets.append(target_library)
    return cirq_targets


TARGETS = find_cirq_targets()


@pytest.mark.parametrize("frontend", TARGETS)
def test_convert_circuit_operation_from_cirq(frontend):
    """Test converting Cirq FrozenCircuit operation to OpenQASM"""
    q = cirq.NamedQubit("q")
    cirq_circuit = cirq.Circuit(
        cirq.Y(q), cirq.CircuitOperation(cirq.FrozenCircuit(cirq.X(q)), repetitions=5), cirq.Z(q)
    )

    graph = ConversionGraph()

    if not graph.has_path("cirq", frontend):
        pytest.skip(f"conversion from cirq to {frontend} not yet supported")

    test_circuit = transpile(cirq_circuit, frontend, conversion_graph=graph)

    cirq_unitary = load_program(cirq_circuit).unitary()

    try:
        test_unitary = load_program(test_circuit).unitary()
    except NotImplementedError:
        pytest.skip(f"Unitary calculation not implemented for {frontend}")

    assert np.allclose(cirq_unitary, test_unitary)


@pytest.mark.parametrize("frontend", TARGETS)
def test_convert_circuit_with_global_phase_from_cirq(frontend):
    """Test converting Cirq circuit with global phase to PyQuil"""
    q0, q1 = cirq.NamedQubit("q0"), cirq.NamedQubit("q1")
    cirq_circuit = cirq.Circuit(cirq.Y(q1).controlled_by(q0))

    graph = ConversionGraph()

    if not graph.has_path("cirq", frontend):
        pytest.skip(f"conversion from cirq to {frontend} not yet supported")

    test_circuit = transpile(cirq_circuit, frontend, conversion_graph=graph)

    try:
        load_program(test_circuit).unitary()
    except NotImplementedError:
        pytest.skip(f"Unitary calculation not implemented for {frontend}")

    assert circuits_allclose(cirq_circuit, test_circuit)

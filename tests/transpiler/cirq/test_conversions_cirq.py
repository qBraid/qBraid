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
Unit tests for the qbraid transpiler conversions module.

"""
from typing import Optional

import cirq
import numpy as np
import pytest

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

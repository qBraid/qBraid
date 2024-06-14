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
Unit test for the graph-based transpiler

"""
import braket.circuits
import pytest

from qbraid.transpiler.converter import transpile
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.exceptions import ConversionPathNotFoundError, NodeNotFoundError
from qbraid.transpiler.graph import ConversionGraph


def test_unuspported_target_package():
    """Test that an error is raised if target package is not supported."""
    with pytest.raises(NodeNotFoundError):
        transpile(braket.circuits.Circuit(), "alice")


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_raise_no_conversion_path_found(bell_circuit):
    """Test raising exception when no conversion path is found"""
    qiskit_circuit, _ = bell_circuit
    conversions = [
        Conversion("cirq", "braket", lambda x: x),
        Conversion("cirq", "qiskit", lambda x: x),
    ]
    graph = ConversionGraph(conversions)
    with pytest.raises(ConversionPathNotFoundError):
        transpile(qiskit_circuit, "braket", conversion_graph=graph)


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_raise_no_conversion_path_found_max_depth(bell_circuit):
    """Test raising exception when no conversion path is found when a conversion path
    exists but does not meet the max_depth requirement."""
    qiskit_circuit, _ = bell_circuit
    with pytest.raises(ConversionPathNotFoundError):
        transpile(qiskit_circuit, "braket", max_path_depth=1, require_native=True)

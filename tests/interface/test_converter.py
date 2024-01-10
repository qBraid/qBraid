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
Unit test for the graph-based transpiler

"""
import braket.circuits
import pytest

from qbraid.transpiler.converter import _get_path_from_bound_methods, convert_to_package
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.exceptions import ConversionPathNotFoundError, NodeNotFoundError
from qbraid.transpiler.graph import ConversionGraph


def test_unuspported_target_package():
    """Test that an error is raised if target package is not supported."""
    with pytest.raises(NodeNotFoundError):
        convert_to_package(braket.circuits.Circuit(), "alice")


def test_get_path_from_bound_method():
    """Test formatted conversion path logging helper function."""
    source, target = "cirq", "qasm2"
    edge = Conversion(source, target, lambda x: x)
    graph = ConversionGraph([edge])
    bound_method = graph[source][target]["func"]
    bound_method_list = [bound_method]
    path = _get_path_from_bound_methods(bound_method_list)
    assert path == "cirq -> qasm2"


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
        convert_to_package(qiskit_circuit, "braket", conversion_graph=graph)


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_raise_no_conversion_path_found_max_depth(bell_circuit):
    """Test raising exception when no conversion path is found when a conversion path
    exists but does not meet the max_depth requirement."""
    qiskit_circuit, _ = bell_circuit
    with pytest.raises(ConversionPathNotFoundError):
        convert_to_package(qiskit_circuit, "braket", max_path_depth=1)

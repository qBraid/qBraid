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

from qbraid.exceptions import PackageValueError
from qbraid.interface.conversion_edge import ConversionEdge
from qbraid.interface.conversion_graph import ConversionGraph
from qbraid.interface.converter import _get_path_from_bound_methods, convert_to_package


def test_unuspported_target_package():
    """Test that an error is raised if target package is not supported."""
    with pytest.raises(PackageValueError):
        convert_to_package(braket.circuits.Circuit(), "alice")


def test_get_path_from_bound_method():
    """Test formatted conversion path logging helper function."""
    source, target = "cirq", "qasm2"
    edge = ConversionEdge(source, target, lambda x: x)
    graph = ConversionGraph([edge])
    bound_method = graph._nx_graph[source][target]["func"]
    bound_method_list = [bound_method]
    path = _get_path_from_bound_methods(bound_method_list)
    assert path == "cirq -> qasm2"

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
Unit test for the graph-based transpiler

"""
import unittest.mock

import braket.circuits
import pytest

from qbraid.programs import register_program_type
from qbraid.transpiler.converter import _warn_if_unsupported, transpile
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.exceptions import ConversionPathNotFoundError, NodeNotFoundError
from qbraid.transpiler.graph import ConversionGraph


def test_unsupported_target_package():
    """Test that an error is raised if target package is not supported."""
    with pytest.raises(NodeNotFoundError):
        transpile(braket.circuits.Circuit(), "alice")


def test_transpile_bad_source():
    """Test raising ValueError for bad source package"""

    def mock_has_node(node):
        """Mock function for has_node"""
        return not node == "fake"

    class FakeClass:
        """Fake class for testing"""

    register_program_type(FakeClass, "fake")
    with unittest.mock.patch(
        "qbraid.transpiler.ConversionGraph.has_node", side_effect=mock_has_node
    ):
        with pytest.raises(NodeNotFoundError):
            transpile(FakeClass(), "cirq")


def test_warning():
    """Test that a warning is raised if the program type is not supported."""
    with pytest.warns(UserWarning):
        _warn_if_unsupported("test", "bad")


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

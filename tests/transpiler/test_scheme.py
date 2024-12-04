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
Unit tests for defining and updating runtime conversion schemes

"""

import pytest
import rustworkx as rx

from qbraid.programs.spec import ProgramSpec
from qbraid.transpiler.graph import ConversionGraph
from qbraid.transpiler.scheme import ConversionScheme


def test_initialization():
    """Test the initialization and default values of the ConversionScheme."""
    cs = ConversionScheme()
    assert cs.conversion_graph is None
    assert cs.max_path_attempts == 3
    assert cs.max_path_depth is None
    assert len(cs.extra_kwargs) == 0


def test_update_values():
    """Test the dynamic update of the ConversionScheme's attributes."""
    cs = ConversionScheme()
    cs.update_values(max_path_attempts=5, max_path_depth=2, extra_kwargs={"new_key": "new_value"})
    assert cs.max_path_attempts == 5
    assert cs.max_path_depth == 2
    assert cs.extra_kwargs == {"new_key": "new_value"}

    # Test updating nested kwargs
    cs.update_values(extra_kwargs={"new_key": "updated_value"})
    assert cs.extra_kwargs["new_key"] == "updated_value"


def test_update_invalid_attribute():
    """Test updating an invalid attribute which should raise an AttributeError."""
    cs = ConversionScheme()
    with pytest.raises(AttributeError):
        cs.update_values(invalid_key="value")


def test_str_method():
    """Test the string representation of the ConversionScheme."""
    cs = ConversionScheme(
        conversion_graph=None,
        max_path_attempts=2,
        max_path_depth=1,
        extra_kwargs={"require_native": True},
    )
    expected_str = (
        "ConversionScheme(conversion_graph=None, max_path_attempts=2, "
        "max_path_depth=1, require_native=True)"
    )
    assert str(cs) == expected_str


@pytest.fixture
def rx_graph():
    """Returns a rustworkx.PyDiGraph for testing."""
    graph = rx.PyDiGraph()
    a = graph.add_node("A")
    b = graph.add_node("B")
    c = graph.add_node("C")
    d = graph.add_node("D")
    e = graph.add_node("E")
    graph.add_edges_from(
        [(a, b, 0.1), (b, c, 1.2), (c, a, 2.0), (d, c, 1.0), (e, d, 2.1), (e, b, 0.2)]
    )
    return graph


@pytest.mark.parametrize(
    "target_node, max_edges, expected_result",
    [
        (["C"], 1, {"C", "B", "D"}),
        (["C"], 2, {"C", "B", "D", "E", "A"}),
        (["A"], 2, {"A", "B", "C", "D"}),
        (["E"], 0, {"E"}),
        (["E", "C"], 1, {"E", "C", "B", "D"}),
        (["A"], None, {"A", "B", "C", "D", "E"}),
    ],
)
def test_find_nodes_reachable_within_max_edges(rx_graph, target_node, max_edges, expected_result):
    """Test finding all nodes reachable from a target node within a specified number of edges."""
    result = ConversionScheme.find_nodes_reachable_within_max_edges(
        rx_graph, target_node, max_edges
    )
    assert result == expected_result


def test_find_nodes_reachable_within_max_edges_raises_for_invalid_target(rx_graph):
    """Test that an error is raised when the target node is not in the graph."""
    with pytest.raises(ValueError) as excinfo:
        ConversionScheme.find_nodes_reachable_within_max_edges(rx_graph, ["F"], 1)
    assert "Target node 'F' not found in the graph." in str(excinfo.value)


def test_update_graph_for_target():
    """Test updating the conversion graph to include only nodes with paths to the target node(s)."""
    qasm2_spec = ProgramSpec(str, alias="qasm2")
    qasm3_spec = ProgramSpec(str, alias="qasm3")

    target_spec = [qasm2_spec, qasm3_spec]

    graph = ConversionGraph(include_isolated=True)

    qasm_nodes = set()
    non_qasm_nodes = set()
    for node in graph.nodes():
        if graph.has_path(node, qasm2_spec.alias) or graph.has_path(node, qasm3_spec.alias):
            qasm_nodes.add(node)
        else:
            non_qasm_nodes.add(node)

    scheme = ConversionScheme(conversion_graph=graph)

    scheme.update_graph_for_target(target_spec)

    updated_graph = scheme.conversion_graph
    assert isinstance(updated_graph, ConversionGraph)

    original_nodes = set(graph.nodes())
    updated_nodes = set(updated_graph.nodes())
    assert updated_nodes == qasm_nodes
    assert len(updated_nodes) == len(original_nodes) - len(non_qasm_nodes)


def test_find_nodes_reachable_within_max_edges_raises_for_negative(rx_graph):
    """Test that an error is raised when the max_edges is negative."""
    with pytest.raises(
        ValueError, match="The maximum number of edges must be a non-negative integer."
    ):
        ConversionScheme.find_nodes_reachable_within_max_edges(rx_graph, ["A"], -1)

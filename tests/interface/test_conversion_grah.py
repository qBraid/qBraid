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
Tests of functions that create and operate on directed graph
used to dictate transpiler conversions.

"""
import networkx as nx
import pytest

from qbraid._qprogram import QPROGRAM_LIBS
from qbraid.interface.conversion_graph import (
    add_new_conversion,
    create_conversion_graph,
    find_shortest_conversion_path,
    find_top_shortest_conversion_paths,
)
from qbraid.transpiler import conversion_functions


def are_graphs_equal(graph1: nx.DiGraph, graph2: nx.DiGraph) -> bool:
    """Return True if two graphs are equal, False otherwise."""
    # Check if nodes are the same
    if set(graph1.nodes) != set(graph2.nodes):
        return False

    # Check if edges are the same
    if set(graph1.edges) != set(graph2.edges):
        return False

    # Check if node attributes are the same
    for node in graph1.nodes:
        if graph1.nodes[node] != graph2.nodes.get(node, {}):
            return False

    # Check if edge attributes are the same
    for edge in graph1.edges:
        if graph1.edges[edge] != graph2.edges.get(edge, {}):
            return False

    return True


@pytest.mark.parametrize("func", conversion_functions)
def test_conversion_functions_syntax(func):
    """Test that all conversion functions are named correctly."""
    source, target = func.split("_to_")
    assert source in QPROGRAM_LIBS
    assert target in QPROGRAM_LIBS
    assert source != target


def test_shortest_conversion_path():
    """Test that the shortest conversion path is found correctly."""
    G = create_conversion_graph(conversion_functions)
    shortest_path = find_shortest_conversion_path(G, "qiskit", "cirq")
    top_paths = find_top_shortest_conversion_paths(G, "qiskit", "cirq", top_n=3)
    assert shortest_path == ["qiskit_to_qasm2", "qasm2_to_cirq"]
    assert shortest_path == top_paths[0]
    assert len(top_paths) == 3 and len(top_paths[0]) <= len(top_paths[1]) <= len(top_paths[2])


def test_add_new_conversion():
    """Test adding a new conversion to the graph."""
    new_conversion_func = "cirq_to_qir"
    graph = create_conversion_graph(conversion_functions)
    updated_graph = add_new_conversion(graph, new_conversion_func)
    expected_graph = create_conversion_graph(conversion_functions + [new_conversion_func])
    assert updated_graph.has_edge("cirq", "qir")
    assert are_graphs_equal(updated_graph, expected_graph)

    shortest_path = find_shortest_conversion_path(updated_graph, "qiskit", "qir")
    assert shortest_path == ["qiskit_to_qasm2", "qasm2_to_cirq", "cirq_to_qir"]

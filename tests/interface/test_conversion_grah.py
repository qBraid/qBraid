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
import braket.circuits
import networkx as nx
import pytest
from qiskit_braket_provider.providers.adapter import convert_qiskit_to_braket_circuit

from qbraid._qprogram import QPROGRAM_LIBS
from qbraid.transpiler.conversions import conversion_functions
from qbraid.transpiler.converter import convert_to_package
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.graph import ConversionGraph


def bound_method_str(source, target):
    """Inserts package names into string representation of bound method."""
    return f"<bound method Conversion.convert of ('{source}', '{target}')>"


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
    G = ConversionGraph()
    shortest_path = G.find_shortest_conversion_path("qiskit", "cirq")
    top_paths = G.find_top_shortest_conversion_paths("qiskit", "cirq", top_n=3)
    assert str(shortest_path[0]) == bound_method_str("qiskit", "qasm2")
    assert str(shortest_path[1]) == bound_method_str("qasm2", "cirq")
    assert shortest_path == top_paths[0]
    assert len(top_paths) == 3 and len(top_paths[0]) <= len(top_paths[1]) <= len(top_paths[2])


def test_add_conversion():
    """
    Test the addition of a new conversion to the ConversionGraph.

    This test checks:
    1. Whether a new conversion edge is correctly added to the graph.
    2. If the graph structure with the new edge matches the expected structure.
    3. The correctness of the shortest conversion path after adding the new edge.
    """
    # Setup - preparing Conversion and ConversionGraph instances
    source, target = "cirq", "qir"
    conversion_func = lambda x: x  # pylint: disable=unnecessary-lambda-assignment
    new_edge = Conversion(source, target, conversion_func)
    initial_conversions = ConversionGraph.load_default_conversions()
    graph_with_new_edge = ConversionGraph(initial_conversions + [new_edge])
    graph_without_new_edge = ConversionGraph(initial_conversions)

    # Action - adding the new conversion edge to the graph
    graph_without_new_edge.add_conversion(new_edge)

    # Assertion 1 - Check if the new edge is added to the graph
    assert graph_without_new_edge.has_edge(source, target)

    # Assertion 2 - Check if the updated graph matches the expected graph structure
    expected_graph = graph_with_new_edge
    updated_graph = graph_without_new_edge
    assert are_graphs_equal(updated_graph, expected_graph)

    # Assertion 3 - Verify the shortest path after adding the new edge
    expected_shortest_path = [
        bound_method_str("qiskit", "qasm2"),
        bound_method_str("qasm2", "cirq"),
        bound_method_str("cirq", "qir"),
    ]
    actual_shortest_path = graph_without_new_edge.find_shortest_conversion_path("qiskit", "qir")
    assert [str(bound_method) for bound_method in actual_shortest_path] == expected_shortest_path


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_initialize_new_conversion(bell_circuit):
    """Test initializing the conversion graph with a new conversion"""
    qiskit_circuit, _ = bell_circuit
    conversions = [
        Conversion(
            "qiskit",
            "braket",
            convert_qiskit_to_braket_circuit,
        )
    ]
    graph = ConversionGraph(conversions)
    assert len(graph.edges) == 1
    braket_circuit = convert_to_package(qiskit_circuit, "braket", conversion_graph=graph)
    assert isinstance(braket_circuit, braket.circuits.Circuit)


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_overwrite_new_conversion(bell_circuit):
    """Test dynamically adding a new conversion  the conversion graph"""
    qiskit_circuit, _ = bell_circuit
    conversions = [Conversion("qiskit", "braket", lambda x: x)]
    graph = ConversionGraph(conversions)
    assert len(graph.edges) == 1
    edge = Conversion("qiskit", "braket", convert_qiskit_to_braket_circuit)
    graph.add_conversion(edge, overwrite=True)
    assert len(graph.edges) == 1
    braket_circuit = convert_to_package(qiskit_circuit, "braket", conversion_graph=graph)
    assert isinstance(braket_circuit, braket.circuits.Circuit)

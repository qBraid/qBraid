# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Tests of functions that create and operate on directed graph
used to dictate transpiler conversions.

"""
from unittest.mock import Mock, PropertyMock, patch

import pytest
import rustworkx as rx
from pyqir import Module

from qbraid.programs import register_program_type
from qbraid.programs.registry import QPROGRAM_ALIASES
from qbraid.transpiler.conversions import conversion_functions
from qbraid.transpiler.conversions.qiskit import qiskit_to_pyqir
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.exceptions import ConversionPathNotFoundError
from qbraid.transpiler.graph import ConversionGraph


@pytest.fixture
def mock_conversions() -> list[Conversion]:
    """List of mock shortest paths for testing."""
    conv1 = Conversion("a", "b", lambda x: x)
    conv2 = Conversion("b", "c", lambda x: x)
    conv3 = Conversion("a", "c", lambda x: x)
    return [conv1, conv2, conv3]


@pytest.fixture
def basic_conversion_graph() -> ConversionGraph:
    """Provides a ConversionGraph with basic conversions setup."""
    conv1 = Conversion("a", "b", lambda x: x)
    conv2 = Conversion("b", "c", lambda x: x)
    conv3 = Conversion("a", "d", lambda x: x)
    graph = ConversionGraph(conversions=[conv1, conv2, conv3])
    return graph


@pytest.fixture
def mock_graph(mock_conversions) -> ConversionGraph:
    """Graph made up of mock paths for testing."""
    return ConversionGraph(conversions=mock_conversions)


def bound_method_str(source, target):
    """Inserts package names into string representation of bound method."""
    return f"<bound method Conversion.convert of ('{source}', '{target}')>"


@pytest.mark.parametrize("func", conversion_functions)
def test_conversion_functions_syntax(func):
    """Test that all conversion functions are named correctly."""
    source, target = func.split("_to_")
    assert source in QPROGRAM_ALIASES
    assert target in QPROGRAM_ALIASES
    assert source != target


def test_shortest_conversion_path():
    """Test that the shortest conversion path is found correctly."""
    G = ConversionGraph(require_native=True)
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
    target = "any"
    conversion_func = lambda x: x  # pylint: disable=unnecessary-lambda-assignment
    new_edge = Conversion("cirq", target, conversion_func)
    conversions = ConversionGraph.load_default_conversions()
    initial_conversions = [e for e in conversions if e.native]
    graph_with_new_edge = ConversionGraph(initial_conversions + [new_edge])
    graph_without_new_edge = ConversionGraph(initial_conversions)

    # Action - adding the new conversion edge to the graph
    graph_without_new_edge.add_conversion(new_edge)

    # Assertion 1 - Check if the new edge is added to the graph
    assert graph_without_new_edge.has_edge("cirq", target)

    # Assertion 2 - Check if the updated graph matches the expected graph structure
    expected_graph = graph_with_new_edge
    updated_graph = graph_without_new_edge
    assert rx.is_isomorphic(updated_graph, expected_graph)

    # Assertion 3 - Verify the shortest path after adding the new edge
    expected_shortest_path = [
        bound_method_str("qiskit", "qasm2"),
        bound_method_str("qasm2", "cirq"),
        bound_method_str("cirq", target),
    ]
    actual_shortest_path = graph_without_new_edge.find_shortest_conversion_path("qiskit", target)
    assert [str(bound_method) for bound_method in actual_shortest_path] == expected_shortest_path


def test_initialize_new_conversion():
    """Test initializing the conversion graph with a new conversion"""
    conversions = [Conversion("qiskit", "pyqir", qiskit_to_pyqir)]
    graph = ConversionGraph(conversions)
    assert graph.num_edges() == 1


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_overwrite_new_conversion(bell_circuit):
    """Test dynamically overwriting a new conversion in the conversion graph"""
    qiskit_circuit, _ = bell_circuit
    conversions = [Conversion("qiskit", "pyqir", lambda x: x)]
    graph = ConversionGraph(conversions)
    assert graph.num_edges() == 1
    edge = Conversion("qiskit", "pyqir", qiskit_to_pyqir)
    graph.add_conversion(edge, overwrite=True)
    assert graph.num_edges() == 1
    module = transpile(qiskit_circuit, "pyqir", conversion_graph=graph)
    assert isinstance(module, Module)


def test_remove_conversion():
    """Test removing a conversion from the ConversionGraph."""
    source, target = "qasm2", "qasm3"
    graph = ConversionGraph()
    num_edges_start = graph.num_edges()
    num_conversions_start = len(graph.conversions())
    assert graph.has_edge(source, target)
    graph.remove_conversion(source, target)
    num_edges_end = graph.num_edges()
    num_conversions_end = len(graph.conversions())
    assert not graph.has_edge(source, target)
    assert num_edges_start - num_edges_end == 1
    assert num_conversions_start - num_conversions_end == 1


def test_copy_conversion_graph():
    """Test copying a ConversionGraph."""
    graph = ConversionGraph()
    graph.add_conversion(Conversion("a", "z", lambda x: x))

    conversions_init = graph.conversions()
    require_native_init = graph.require_native
    node_alias_id_map_init = graph._node_alias_id_map

    copy = graph.copy()

    assert conversions_init == copy.conversions()
    assert require_native_init == copy.require_native
    assert node_alias_id_map_init == copy._node_alias_id_map


def test_get_path_from_bound_method():
    """Test formatted conversion path logging helper function."""
    source, target = "cirq", "qasm2"
    edge = Conversion(source, target, lambda x: x)
    graph = ConversionGraph([edge])
    edge_data = graph.get_edge_data(
        graph._node_alias_id_map[source], graph._node_alias_id_map[target]
    )
    bound_method = edge_data["func"]
    bound_method_list = [bound_method]
    path = ConversionGraph._get_path_from_bound_methods(bound_method_list)
    assert path == "cirq -> qasm2"


def test_raise_index_error_bound_methods_empty():
    """Test raising ValueError when bound_methods is empty."""
    with pytest.raises(IndexError):
        ConversionGraph._get_path_from_bound_methods([])


def test_attr_error_bound_method_no_source_target():
    """Test raising AttributeError when bound_methods has no source or target."""
    with pytest.raises(AttributeError):
        ConversionGraph._get_path_from_bound_methods([Mock()])


def test_shortest_path(mock_graph):
    """Test the string representation of the shortest path."""
    path = mock_graph.shortest_path("a", "c")
    assert path == "a -> c"


def test_all_paths(mock_graph):
    """Test the string representation of the shortest path."""
    paths = mock_graph.all_paths("a", "c")
    assert isinstance(paths, list)
    assert len(paths) == 2
    assert "a -> b -> c" in paths
    assert "a -> c" in paths


def test_raise_error_for_no_conversion_path(basic_conversion_graph):
    """Test raising an error when there are no possible
    conversion paths between two nodes that do not have a direct path."""
    with pytest.raises(ConversionPathNotFoundError):
        basic_conversion_graph.find_shortest_conversion_path("b", "d")
    with pytest.raises(ConversionPathNotFoundError):
        basic_conversion_graph.find_top_shortest_conversion_paths("b", "d")


def test_raise_error_for_add_conversion_that_already_exists(basic_conversion_graph):
    """Test raising an error when trying to add a conversion that already exists."""
    conv1 = Conversion("a", "b", lambda x: x)
    with pytest.raises(ValueError):
        basic_conversion_graph.add_conversion(conv1)


def test_raise_error_for_remove_conversion_that_does_not_exist(basic_conversion_graph):
    """Test raising an error when trying to remove a conversion that does not exist."""
    with pytest.raises(ValueError):
        basic_conversion_graph.remove_conversion("a", "c")


def test_reset_conversion_graph():
    """Test resetting the ConversionGraph to its default state."""
    graph = ConversionGraph()
    graph.add_conversion(Conversion("a", "b", lambda x: x))
    num_conversions = len(graph.conversions())
    graph.reset()
    num_conversions_after_reset = len(graph.conversions())
    assert num_conversions_after_reset == num_conversions - 1


def test_raise_attribute_error_no_source():
    """
    Test raising an AttributeError when there is no source
    attribute in bound method.

    """
    with pytest.raises(AttributeError):
        ConversionGraph._get_path_from_bound_methods([lambda x: x])


def test_has_path_does_not_exist():
    """Test that has_path returns False when there is no path between two existing nodes."""

    class DummyA:
        """Dummy class for testing."""

    class DummyB:
        """Dummy class for testing."""

    register_program_type(DummyA, "a")
    register_program_type(DummyB, "b")
    graph = ConversionGraph()
    assert not graph.has_path("a", "b")


def test_get_path_from_bound_methods_attribute_error():
    """Test that AttributeError is raised when bound methods
    lack 'source' or 'target' attributes."""
    conversion = Conversion("a", "b", lambda x: x)
    graph = ConversionGraph()
    graph.add_conversion(conversion)

    data = graph.get_edge_data(graph._node_alias_id_map["a"], graph._node_alias_id_map["b"])
    func = data["func"].__self__

    with (
        patch.object(type(func), "source", new_callable=PropertyMock, side_effect=AttributeError),
        patch.object(type(func), "target", new_callable=PropertyMock, side_effect=AttributeError),
    ):
        with pytest.raises(AttributeError) as excinfo:
            graph._get_path_from_bound_methods([data["func"]])

        assert "Bound method instance lacks 'source' or 'target' attributes." in str(excinfo.value)

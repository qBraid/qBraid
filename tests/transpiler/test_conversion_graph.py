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
import importlib.util
from unittest.mock import Mock, PropertyMock, patch

import pytest
import rustworkx as rx

try:
    import pyqir

    pyqir_installed = True
except ImportError:
    pyqir_installed = False

from qbraid.programs import ExperimentType, register_program_type, unregister_program_type
from qbraid.programs.ahs import submodules as ahs_submodules
from qbraid.programs.annealing import submodules as annealing_submodules
from qbraid.programs.gate_model import submodules as gate_model_submodules
from qbraid.programs.registry import QPROGRAM_ALIASES, QPROGRAM_REGISTRY
from qbraid.transpiler.conversions import conversion_functions
from qbraid.transpiler.conversions.qiskit import qiskit_to_pyqir
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.exceptions import ConversionPathNotFoundError
from qbraid.transpiler.graph import ConversionGraph, _get_path_from_bound_methods

qiskit_qir_installed = importlib.util.find_spec("qiskit_qir") is not None


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
    graph = ConversionGraph(conversions=[conv1, conv2, conv3], include_isolated=False)
    return graph


@pytest.fixture
def mock_graph(mock_conversions) -> ConversionGraph:
    """Graph made up of mock paths for testing."""
    return ConversionGraph(conversions=mock_conversions)


@pytest.fixture
def native_conversion_graph():
    """Returns a ConversionGraph with only native conversions."""
    return ConversionGraph(require_native=True, include_isolated=False)


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


def test_shortest_conversion_path(native_conversion_graph: ConversionGraph):
    """Test that the shortest conversion path is found correctly."""
    shortest_path = native_conversion_graph.find_shortest_conversion_path("qiskit", "cirq")
    top_paths = native_conversion_graph.find_top_shortest_conversion_paths(
        "qiskit", "cirq", top_n=3
    )
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


@pytest.mark.skipif(not qiskit_qir_installed, reason="qiskit_qir not installed")
def test_initialize_new_conversion():
    """Test initializing the conversion graph with a new conversion"""
    conversions = [Conversion("qiskit", "pyqir", qiskit_to_pyqir)]
    graph = ConversionGraph(conversions)
    assert graph.num_edges() == 1


@pytest.mark.skipif(
    not all([pyqir_installed, qiskit_qir_installed]), reason="pyqir or qiskit_qir not installed"
)
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
    assert isinstance(module, pyqir.Module)


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
    graph = ConversionGraph(include_isolated=False)
    graph.add_conversion(Conversion("a", "z", lambda x: x))

    conversions_init = graph.conversions()
    require_native_init = graph.require_native
    node_alias_id_map_init = graph._node_alias_id_map

    copy = graph.copy()

    assert conversions_init == copy.conversions()
    assert require_native_init == copy.require_native
    assert node_alias_id_map_init == copy._node_alias_id_map


@pytest.mark.parametrize("program_type", ["qasm2", "qasm3", "pyquil", "braket", "cirq"])
def test_unregistered_node_in_conversion_graph(program_type):
    """Test the unregistered nodes in ConversionGraph"""
    if program_type not in QPROGRAM_ALIASES:
        pytest.skip(f"{program_type} not installed")

    graph = ConversionGraph()
    assert graph.has_node(program_type) is True

    # Backup QPROGRAM registry
    aliases_backup = QPROGRAM_ALIASES.copy()
    registry_backup = QPROGRAM_REGISTRY.copy()
    unregister_program_type(program_type)

    new_graph = ConversionGraph()
    assert new_graph.has_node(program_type) is False

    # Revert changes.
    QPROGRAM_ALIASES.clear()
    QPROGRAM_ALIASES.update(aliases_backup)
    QPROGRAM_REGISTRY.clear()
    QPROGRAM_REGISTRY.update(registry_backup)


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
    path = _get_path_from_bound_methods(bound_method_list)
    assert path == "cirq -> qasm2"


def test_raise_index_error_bound_methods_empty():
    """Test raising ValueError when bound_methods is empty."""
    with pytest.raises(IndexError):
        _get_path_from_bound_methods([])


def test_attr_error_bound_method_no_source_target():
    """Test raising AttributeError when bound_methods has no source or target."""
    with pytest.raises(AttributeError):
        _get_path_from_bound_methods([Mock()])


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
        _get_path_from_bound_methods([lambda x: x])


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
            _get_path_from_bound_methods([data["func"]])

        assert "Bound method instance lacks 'source' or 'target' attributes." in str(excinfo.value)


def test_closest_target_direct_match(basic_conversion_graph: ConversionGraph):
    """Test that a direct conversion is returned when available."""
    assert basic_conversion_graph.closest_target("a", ["a", "b"]) == "a"


def test_closest_target_shortest_path_selection(basic_conversion_graph: ConversionGraph):
    """Test that the shortest path is selected when multiple paths are available."""
    assert basic_conversion_graph.closest_target("a", ["b", "c"]) == "b"


def test_closest_target_no_paths(basic_conversion_graph: ConversionGraph):
    """Test that None is returned when no paths are available."""
    assert basic_conversion_graph.closest_target("c", ["a", "b"]) is None


def test_closest_target_no_targets(basic_conversion_graph: ConversionGraph):
    """Test that None is returned when no targets are available."""
    assert basic_conversion_graph.closest_target("a", []) is None


@pytest.mark.parametrize(
    "submodules, expected_type",
    [
        (gate_model_submodules, ExperimentType.GATE_MODEL),
        (ahs_submodules, ExperimentType.AHS),
        (annealing_submodules, ExperimentType.ANNEALING),
    ],
)
def test_get_native_node_experiment_types(
    submodules, expected_type, native_conversion_graph: ConversionGraph
):
    """Test that the native conversion graph has the correct experiment types for each node."""
    node_to_exp_type = native_conversion_graph.get_node_experiment_types()
    for node in submodules:
        assert node not in node_to_exp_type or node_to_exp_type[node] == expected_type


def test_get_node_experiment_type_other(basic_conversion_graph: ConversionGraph):
    """Test that the experiment type is 'OTHER' for nodes with no path to a native node."""
    node_to_exp_type = basic_conversion_graph.get_node_experiment_types()
    for node in basic_conversion_graph.nodes():
        assert node_to_exp_type[node] == ExperimentType.OTHER


def test_register_annealing_conversion_and_check_experiment_type():
    """Test that the experiment type is correctly set for a new annealing conversion."""
    conversion_other = Conversion("a", "b", lambda x: x)
    conversion_annealing = Conversion("qubo", "mock_type", lambda x: x)
    graph = ConversionGraph(
        conversions=[conversion_annealing, conversion_other], include_isolated=False
    )
    node_to_exp_type = graph.get_node_experiment_types()
    assert node_to_exp_type == {
        "a": ExperimentType.OTHER,
        "b": ExperimentType.OTHER,
        "qubo": ExperimentType.ANNEALING,
        "mock_type": ExperimentType.ANNEALING,
    }


def test_get_node_experiment_type_raises_for_conflicting_experiment_types():
    """Test that an error is raised when the experiment types of two nodes conflict."""
    conversion_gate_model = Conversion("a", "qasm2", lambda x: x)
    conversion_annealing = Conversion("qubo", "a", lambda x: x)
    graph = ConversionGraph(conversions=[conversion_annealing, conversion_gate_model])
    with pytest.raises(ValueError) as excinfo:
        graph.get_node_experiment_types()
    assert "ExperimentType conflict" in str(excinfo.value)


def test_include_isolated_nodes():
    """Test including isolated nodes in the conversion graph."""
    graph = ConversionGraph(include_isolated=False)
    graph2 = ConversionGraph(include_isolated=True)

    assert "qubo" not in graph.nodes()
    assert "qubo" in graph2.nodes()


@pytest.mark.parametrize(
    "nodes, include_isolated, expected_nodes",
    [
        (["qasm2", "qasm3"], False, ["qasm2", "qasm3"]),
        (["qasm2", "qasm3", "qubo"], False, ["qasm2", "qasm3"]),
        (["qasm2", "qasm3", "qubo"], True, ["qasm2", "qasm3", "qubo"]),
    ],
)
def test_create_graph_node_options(nodes, include_isolated, expected_nodes):
    """Test creating a conversion graph invoking different node options."""
    graph = ConversionGraph(nodes=nodes, include_isolated=include_isolated)
    assert set(graph.nodes()) == set(expected_nodes)


def test_subgraph_by_experiment_type():
    """Test creating a subgraph by experiment type."""
    annealing_nodes = ["qubo"]
    gate_model_nodes = ["qasm2", "qasm3"]
    nodes = gate_model_nodes + annealing_nodes
    graph = ConversionGraph(nodes=nodes, include_isolated=True)

    identical_subgraph = graph.subgraph([ExperimentType.GATE_MODEL, ExperimentType.ANNEALING])
    assert set(identical_subgraph.nodes()) == set(nodes)

    gate_model_subgraph = graph.subgraph(ExperimentType.GATE_MODEL)
    assert set(gate_model_subgraph.nodes()) == set(gate_model_nodes)

    annealing_subgraph = graph.subgraph(ExperimentType.ANNEALING)
    assert set(annealing_subgraph.nodes()) == set(annealing_nodes)

    with pytest.raises(ValueError) as excinfo:
        graph.subgraph(ExperimentType.OTHER)
    assert "No program type nodes found with experiment type(s)" in str(excinfo.value)

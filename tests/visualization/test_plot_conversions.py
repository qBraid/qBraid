# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=unused-argument,redefined-outer-name
"""
Unit tests for plotting conversion graphs

"""
import warnings
from unittest.mock import MagicMock, patch

import pytest

from qbraid.programs.experiment import ExperimentType
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.graph import ConversionGraph
from qbraid.visualization.plot_conversions import plot_conversion_graph


@pytest.fixture
def mock_graph():
    """Mock graph object for testing plot_conversion_graph."""
    mock = MagicMock()
    mock.nodes.return_value = ["node1", "node2"]
    mock.conversions.return_value = []
    mock.edge_list.return_value = []
    mock.get_node_data.return_value = "node_data"
    mock.get_edge_data.return_value = {"native": True}
    mock._node_alias_id_map = {"node1": 1, "node2": 2}
    return mock


@patch("qbraid.visualization.plot_conversions.plt", autospec=True)
@patch(
    "qbraid.visualization.plot_conversions.rx.spring_layout",
    return_value={"node1": (0, 0), "node2": (1, 1)},
    autospec=True,
)
@patch("qbraid.visualization.plot_conversions.rx.visualization.mpl_draw", autospec=True)
def test_plot_conversion_graph_show(mock_draw, mock_layout, mock_plt, mock_graph):
    """Test that the graph is displayed when show is True and not saved."""
    plot_conversion_graph(graph=mock_graph, show=True, edge_labels=True)
    mock_plt.show.assert_called_once()
    mock_plt.savefig.assert_not_called()


@patch("qbraid.visualization.plot_conversions.plt", autospec=True)
@patch("qbraid.visualization.plot_conversions.rx.spring_layout", autospec=True)
@patch("qbraid.visualization.plot_conversions.rx.visualization.mpl_draw", autospec=True)
def test_plot_conversion_graph_save(mock_draw, mock_layout, mock_plt, mock_graph):
    """Test that the graph is saved to the correct path when specified."""
    save_path = "path/to/save/plot.png"
    plot_conversion_graph(graph=mock_graph, show=False, save_path=save_path)
    mock_plt.savefig.assert_called_once_with(save_path)
    mock_plt.show.assert_not_called()


@patch("qbraid.visualization.plot_conversions.plt", autospec=True)
@patch("qbraid.visualization.plot_conversions.rx.spring_layout", autospec=True)
@patch("qbraid.visualization.plot_conversions.rx.visualization.mpl_draw", autospec=True)
def test_plot_conversion_graph_with_custom_title_and_legend(
    mock_draw, mock_layout, mock_plt, mock_graph
):
    """Test custom title and legend are set correctly."""
    title = "Custom Graph Title"
    plot_conversion_graph(graph=mock_graph, title=title, legend=True, show=False)
    mock_plt.title.assert_called_once_with(title)
    mock_plt.legend.assert_called_once()


@patch("qbraid.visualization.plot_conversions.plt", autospec=True)
@patch("qbraid.visualization.plot_conversions.rx.visualization.mpl_draw", autospec=True)
def test_invoke_plot_method_from_conversion_graph(mock_draw, mock_plt):
    """Test that the graph is displayed when invoked via ConversionGraph.plot method."""
    graph = ConversionGraph()

    with pytest.warns(UserWarning, match=r"Detected multiple edge colors*"):
        graph.plot(show=True)
        mock_plt.show.assert_called_once()


def test_plot_conversion_graph_warning():
    """Test that a warning is raised when multiple edge colors are detected."""
    with patch("rustworkx.__version__", "0.15.0"):
        graph = ConversionGraph()

        graph.add_conversion(Conversion("node1", "node2", lambda x: x))

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            plot_conversion_graph(graph, show=False)
            assert any(
                "Detected multiple edge colors, which may not display correctly"
                in str(warning.message)
                for warning in w
            )


def test_plot_conversion_graph_experiment_type_raises_for_none_found():
    """Test that an exception is raised when no matching experiment type is found."""
    graph = ConversionGraph(nodes=["qasm2", "qasm3"])

    with pytest.raises(ValueError) as exc:
        plot_conversion_graph(graph, experiment_type=ExperimentType.ANNEALING)
    assert "No program type nodes found" in str(exc.value)


@patch("qbraid.visualization.plot_conversions.is_registered_alias_native", autospec=True)
def test_plot_conversion_graph_valid_experiment_type(is_registered_alias_native):
    """Test plotting a conversion graph based on a valid experiment type."""
    nodes = ["qasm2", "qasm3", "qubo"]
    conversions = [Conversion("qasm2", "qasm3", lambda x: x)]
    graph = ConversionGraph(conversions=conversions, nodes=nodes, include_isolated=True)

    plot_conversion_graph(graph, experiment_type=ExperimentType.ANNEALING, show=False)
    is_registered_alias_native.assert_called_once_with("qubo")

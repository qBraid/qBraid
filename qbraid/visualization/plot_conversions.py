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
Module for plotting qBraid transpiler quantum program conversion graphs.

"""
from typing import TYPE_CHECKING, Dict, Optional

import matplotlib.pyplot as plt
import networkx as nx

from qbraid.programs._import import QPROGRAM_LIBS

if TYPE_CHECKING:
    import qbraid.transpiler


def plot_conversion_graph(  # pylint: disable=too-many-arguments
    graph: "qbraid.transpiler.ConversionGraph",
    title: Optional[str] = "qBraid Quantum Program Conversion Graph",
    legend: bool = False,
    seed: Optional[int] = None,
    node_size: int = 1200,
    min_target_margin: int = 18,
    show: bool = True,
    save_path: Optional[str] = None,
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """
    Plot the conversion graph using matplotlib. The graph is displayed using node
    and edge color conventions, with options for a title, legend, and figure saving.

    Args:
        graph (qbraid.interface.ConversionGraph): The directed conversion graph to be plotted.
        title (Optional[str]): Title of the plot. Defaults to
                               'qBraid Quantum Program Conversion Graph'.
        legend (bool): If True, display a legend on the graph. Defaults to False.
        seed (Optional[int]): Seed for the node layout algorithm. Useful for consistent positioning.
                              Defaults to None.
        node_size (int): Size of the nodes. Defaults to 1200.
        min_target_margin (int): Minimum target margin for edges. Defaults to 18.
        show (bool): If True, display the figure. Defaults to True.
        save_path (Optional[str]): Path to save the figure. If None, the figure is not saved.
                                   Defaults to None.
        colors (Optional[Dict[str, str]]): Dictionary for node and edge colors. Expected keys are
            'qbraid_node', 'external_node', 'qbraid_edge', 'external_edge'. Defaults to None.

    Returns:
        None
    """
    # Set default colors if not provided
    if colors is None:
        colors = {
            "qbraid_node": "lightblue",
            "external_node": "lightgray",
            "qbraid_edge": "gray",
            "external_edge": "blue",
        }

    # Extract colors and apply them in the drawing
    ncolors = [
        colors["qbraid_node"] if node in QPROGRAM_LIBS else colors["external_node"]
        for node in graph.nodes()
    ]

    # Create a dictionary for quick lookup of conversions by their source and target
    conversion_dict = {
        (conversion.source, conversion.target): conversion for conversion in graph.conversions()
    }
    conversions_ordered = [
        conversion_dict[(edge[0], edge[1])]
        for edge in graph.edges()
        if (edge[0], edge[1]) in conversion_dict
    ]
    ecolors = [
        (
            colors["qbraid_edge"]
            if graph[edge.source][edge.target]["native"]
            else colors["external_edge"]
        )
        for edge in conversions_ordered
    ]

    pos = nx.spring_layout(graph, seed=seed)  # good seeds: 123, 134
    nx.draw_networkx_nodes(graph, pos, node_color=ncolors, node_size=node_size)
    nx.draw_networkx_edges(graph, pos, edge_color=ecolors, min_target_margin=min_target_margin)
    nx.draw_networkx_labels(graph, pos)

    if title:
        plt.title(title)
    plt.axis("off")

    if legend:
        # Create legend elements using a loop
        legend_info = [
            ("qBraid - Node", "o", colors["qbraid_node"], None),
            ("External - Node", "o", colors["external_node"], None),
            ("qBraid - Edge", None, colors["qbraid_edge"], "-"),
            ("External - Edge", None, colors["external_edge"], "-"),
        ]
        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                marker=marker,
                color="w" if marker else color,
                label=label,
                markersize=10 if marker else None,
                markerfacecolor=color if marker else None,
                linestyle=linestyle,
                linewidth=2 if linestyle else None,
            )
            for label, marker, color, linestyle in legend_info
        ]
        plt.legend(handles=legend_elements, loc="best")

    if show:
        plt.show()

    if save_path:
        plt.savefig(save_path)

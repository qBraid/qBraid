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
Module for plotting qBraid transpiler quantum program conversion graphs.

"""
from typing import TYPE_CHECKING, Optional

import rustworkx as rx
from qbraid_core._import import LazyLoader

from qbraid.programs.registry import is_registered_alias_native

if TYPE_CHECKING:
    import qbraid.transpiler

plt = LazyLoader("plt", globals(), "matplotlib.pyplot")


def plot_conversion_graph(  # pylint: disable=too-many-arguments
    graph: "qbraid.transpiler.ConversionGraph",
    title: Optional[str] = "qBraid Quantum Program Conversion Graph",
    legend: bool = False,
    seed: Optional[int] = None,
    node_size: int = 1200,
    min_target_margin: int = 18,
    show: bool = True,
    save_path: Optional[str] = None,
    colors: Optional[dict[str, str]] = None,
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
        colors (Optional[dict[str, str]]): Dictionary for node and edge colors. Expected keys are
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
            "extras_edge": "red",
        }

    # Extract colors and apply them in the drawing
    ncolors = [
        colors["qbraid_node"] if is_registered_alias_native(node) else colors["external_node"]
        for node in graph.nodes()
    ]

    # Create a dictionary for quick lookup of conversions by their source and target
    conversion_dict = {
        (conversion.source, conversion.target): conversion for conversion in graph.conversions()
    }
    conversions_ordered = [
        conversion_dict[(graph.get_node_data(edge[0]), graph.get_node_data(edge[1]))]
        for edge in graph.edge_list()
        if (graph.get_node_data(edge[0]), graph.get_node_data(edge[1])) in conversion_dict
    ]
    ecolors = [
        (
            colors["qbraid_edge"]
            if graph.get_edge_data(
                graph._node_str_to_id[edge.source], graph._node_str_to_id[edge.target]
            )["native"]
            else colors["extras_edge"] if len(edge._extras) > 0 else colors["external_edge"]
        )
        for edge in conversions_ordered
    ]

    pos = rx.spring_layout(graph, seed=seed)  # good seeds: 123, 134
    rx.visualization.mpl_draw(
        graph,
        pos,
        node_color=ncolors,
        edge_color=ecolors,
        node_size=node_size,
        with_labels=True,
        labels=str,
        min_target_margin=min_target_margin,
    )

    if title:
        plt.title(title)
    plt.axis("off")

    if legend:
        # Create legend elements using a loop
        legend_info = [
            ("qBraid - Node", "o", colors["qbraid_node"], None),
            ("External - Node", "o", colors["external_node"], None),
            ("qBraid - Edge", None, colors["qbraid_edge"], "-"),
            ("Extras - Edge", None, colors["extras_edge"], "-"),
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

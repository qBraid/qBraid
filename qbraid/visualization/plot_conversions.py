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
from __future__ import annotations

import math
import random
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional

import rustworkx as rx
from qbraid_core._import import LazyLoader
from rustworkx.visualization import mpl_draw

from qbraid.programs.experiment import ExperimentType
from qbraid.programs.registry import is_registered_alias_native

if TYPE_CHECKING:
    import matplotlib.pyplot

    import qbraid.runtime
    import qbraid.transpiler

plt: matplotlib.pyplot = LazyLoader("plt", globals(), "matplotlib.pyplot")

transpiler: qbraid.transpiler = LazyLoader("transpiler", globals(), "qbraid.transpiler")


def _validate_colors(colors: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Validate and return the colors dictionary."""
    default_colors = {
        "target_node_outline": "red",
        "qbraid_node": "lightblue",
        "external_node": "lightgray",
        "qbraid_edge": "gray",
        "external_edge": "blue",
        "extras_edge": "darkgrey",
    }

    if colors is None:
        return default_colors

    extra_keys = set(colors.keys()) - set(default_colors.keys())
    if extra_keys:
        raise ValueError(f"Unexpected keys in 'colors': {extra_keys}")

    for key, value in default_colors.items():
        if key not in colors:
            colors[key] = value

    return colors


def plot_conversion_graph(  # pylint: disable=too-many-arguments
    graph: qbraid.transpiler.ConversionGraph,
    title: Optional[str] = "qBraid Quantum Program Conversion Graph",
    legend: bool = False,
    seed: Optional[int] = None,
    node_size: int = 1200,
    min_target_margin: int = 18,
    ax_margins: float = 0.1,
    show: bool = True,
    save_path: Optional[str | Path] = None,
    colors: Optional[dict[str, str]] = None,
    edge_labels: bool = False,
    experiment_type: Optional[ExperimentType | Iterable[ExperimentType]] = None,
    target_nodes: Optional[Iterable[str]] = None,
    **kwargs,
) -> None:
    """
    Plot the conversion graph using matplotlib. The graph is displayed using node
    and edge color conventions, with options for a title, legend, and figure saving.

    Args:
        graph (ConversionGraph): The directed conversion graph to be plotted.
        title (str | None): Title of the plot. Defaults to
            'qBraid Quantum Program Conversion Graph'.
        legend (bool): If True, display a legend on the graph. Defaults to False.
        seed (int | None): Seed for the node layout algorithm. Useful for consistent
            positioning. Defaults to None.
        node_size (int): Size of the nodes. Defaults to 1200.
        min_target_margin (int): Minimum target margin for edges. Defaults to 18.
        ax_margins (float): Padding added (as a fraction of data range) to auto-scaled
            axis limits. Defaults to 0.1.
        show (bool): If True, display the figure. Defaults to True.
        save_path (str | Path | None): Path to save the figure. If None, figure is not saved.
        colors (dict[str, str] | None): Node and edge colors with keys 'target_node_outline',
            'qbraid_node', 'external_node', 'qbraid_edge', 'external_edge'. Defaults to None.
        edge_labels (bool): If True, display edge weights as labels. Defaults to False.
        experiment_type (ExperimentType | Iterable[ExperimentType] | None): Filter the
            graph by experiment type. Defaults to None, meaning all experiment types are included.
        target_nodes (Iterable[str] | None): Nodes to be outlined in the plot. Defaults to None.

    Returns:
        None
    """
    colors = _validate_colors(colors)

    if experiment_type:
        graph = graph.subgraph(experiment_type)

    ncolors = [
        colors["qbraid_node"] if is_registered_alias_native(node) else colors["external_node"]
        for node in graph.nodes()
    ]

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
                graph._node_alias_id_map[edge.source], graph._node_alias_id_map[edge.target]
            )["native"]
            else colors["extras_edge"] if len(edge._extras) > 0 else colors["external_edge"]
        )
        for edge in conversions_ordered
    ]

    rustworkx_version = rx.__version__  # pylint: disable=no-member
    if len(set(ecolors)) > 1 and rustworkx_version in ["0.15.0", "0.15.1"]:
        warnings.warn(
            "Detected multiple edge colors, which may not display correctly "
            "due to a known bug in rustworkx>=0.15.0,<0.16.0 "
            "(see: https://github.com/Qiskit/rustworkx/issues/1308). "
            "To avoid this issue, please upgrade to rustworkx>=0.16.0.",
            UserWarning,
        )
    seed = seed or random.randint(1, 999)
    k = kwargs.pop("k", max(1 / math.sqrt(len(graph.nodes())), 3))
    pos = rx.spring_layout(graph, seed=seed, k=k, **kwargs)
    kwargs = {}
    if edge_labels:
        kwargs["edge_labels"] = lambda edge: round(edge["weight"], 2)

    if target_nodes:
        edgecolors = [
            colors["target_node_outline"] if node in target_nodes else color
            for node, color in zip(graph.nodes(), ncolors)
        ]

        kwargs["edgecolors"] = edgecolors

    plt.ioff()  # Disable interactive mode

    fig = plt.figure()
    ax = fig.add_subplot(111)

    mpl_draw(
        graph,
        pos,
        ax=ax,
        node_color=ncolors,
        edge_color=ecolors,
        node_size=node_size,
        with_labels=True,
        labels=str,
        min_target_margin=min_target_margin,
        **kwargs,
    )

    ax.margins(ax_margins, ax_margins)

    if title:
        plt.title(title)
    plt.axis("on")

    if legend:
        legend_info = [
            (
                ("Target - Node", "o", colors["target_node_outline"], "white", None)
                if target_nodes
                else None
            ),
            (
                ("qBraid - Node", "o", None, colors["qbraid_node"], None)
                if colors["qbraid_node"] in ncolors
                else None
            ),
            (
                ("External - Node", "o", None, colors["external_node"], None)
                if colors["external_node"] in ncolors
                else None
            ),
            (
                ("qBraid - Edge", None, None, colors["qbraid_edge"], "-")
                if colors["qbraid_edge"] in ecolors
                else None
            ),
            (
                ("Extras - Edge", None, None, colors["extras_edge"], "-")
                if colors["extras_edge"] in ecolors
                else None
            ),
            (
                ("External - Edge", None, None, colors["external_edge"], "-")
                if colors["external_edge"] in ecolors
                else None
            ),
        ]

        legend_info = [entry for entry in legend_info if entry is not None]

        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                marker=marker,
                color="w" if marker else color,
                label=label,
                markersize=10 if marker else None,
                markeredgecolor=edgecolor if marker else None,
                markerfacecolor=color if marker else None,
                linestyle=linestyle,
                linewidth=2 if linestyle else None,
            )
            for label, marker, edgecolor, color, linestyle in legend_info
        ]
        plt.legend(handles=legend_elements, loc="best")

        text = f"seed: {seed}"

        plt.text(
            x=0.01,
            y=0.01,
            s=text,
            transform=plt.gca().transAxes,
            fontsize=8,
            color="gray",
            ha="left",
            va="bottom",
        )

    fig.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=300)

    if show:
        plt.show(block=True)  # Explicit blocking show


def plot_runtime_conversion_scheme(device: qbraid.runtime.QuantumDevice, **kwargs) -> None:
    """
    Plot the runtime conversion scheme for a given quantum device.

    Args:
        device (QuantumDevice): The quantum device for which to plot the conversion scheme.
        **kwargs: Additional keyword arguments to pass to the plotting function.

    Returns:
        None
    """
    if device.profile.program_spec:
        device.scheme.reset_graph()
        device.scheme.update_graph_for_target(device.profile.program_spec)

    graph = device.scheme.conversion_graph
    experiment_type = device.profile.experiment_type
    target_spec = device.profile.program_spec

    target_nodes = (
        {spec.alias for spec in (target_spec if isinstance(target_spec, list) else [target_spec])}
        if target_spec
        else None
    )

    title = kwargs.pop("title", f"Runtime Conversion Scheme for {str(device)}")

    plot_conversion_graph(
        graph,
        title=title,
        experiment_type=experiment_type,
        target_nodes=target_nodes,
        **kwargs,
    )

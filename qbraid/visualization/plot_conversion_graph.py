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
Module for plotting the graph of all transpiler conversion functions using networkx.

"""

import matplotlib.pyplot as plt
import networkx as nx


def plot_conversion_graph(graph: nx.Graph) -> None:
    """
    Plot the conversion graph using matplotlib.

    Args:
        graph (nx.Graph): The graph to be plotted.

    Returns:
        None
    """
    pos = nx.spring_layout(graph, seed=123)
    nx.draw_networkx_nodes(graph, pos, node_color="lightblue", node_size=1200)
    nx.draw_networkx_edges(graph, pos, edge_color="gray", min_target_margin=18)
    nx.draw_networkx_labels(graph, pos)
    plt.title("qBraid Quantum Program Conversion Graph")
    plt.axis("off")
    plt.show()

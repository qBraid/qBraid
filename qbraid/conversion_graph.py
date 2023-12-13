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
Module providing tools to map, analyze, and visualize conversion paths between different
quantum programs available through the qbraid.transpiler using directed graphs.

"""
from typing import List

import networkx as nx


def create_conversion_graph(conversion_funcs: List[str]) -> nx.DiGraph:
    """
    Create a directed graph from a list of conversion functions.

    Args:
        conversion_functions (list of str): List of conversion function names.

    Returns:
        nx.DiGraph: The directed graph created from conversion functions.
    """
    graph = nx.DiGraph()
    for func in conversion_funcs:
        source, target = func.split("_to_")
        graph.add_edge(source, target)
    return graph


def add_new_conversion(graph: nx.DiGraph, conversion_func: str) -> nx.DiGraph:
    """
    Add a new conversion function as an edge in the graph.

    Args:
        graph (nx.DiGraph): The graph to add the conversion to.
        conversion_func (str): The conversion function name.

    Returns:
        nx.DiGraph: The graph with the new conversion added.
    """
    source, target = conversion_func.split("_to_")
    if not graph.has_edge(source, target):
        graph.add_edge(source, target)
    return graph


def find_shortest_conversion_path(graph: nx.DiGraph, source: str, target: str) -> List[str]:
    """
    Find the shortest conversion path between two nodes in a graph.

    Args:
        graph (nx.Graph): The graph representing conversion paths.
        source (str): The starting node for the path.
        target (str): The target node for the path.

    Returns:
        list of str: The shortest conversion path as a list of step strings.

    Raises:
        ValueError: If no path is found between source and target.
    """
    try:
        path = nx.shortest_path(graph, source, target)
        return [f"{path[i]}_to_{path[i+1]}" for i in range(len(path) - 1)]
    except nx.NetworkXNoPath as err:
        raise ValueError(f"No conversion path available between {source} and {target}.") from err


def find_top_shortest_conversion_paths(
    graph: nx.DiGraph, source: str, target: str, top_n: int = 3
) -> List[List[str]]:
    """
    Find the top shortest conversion paths between two nodes in a graph.

    Args:
        graph (nx.Graph): The graph representing conversion paths.
        source (str): The starting node for the path.
        target (str): The target node for the path.
        top_n (int): Number of top shortest paths to find.

    Returns:
        list of list of str: The top shortest conversion paths.

    Raises:
        ValueError: If no path is found between source and target.
    """
    try:
        all_paths = list(nx.all_simple_paths(graph, source, target))
        sorted_paths = sorted(all_paths, key=len)[:top_n]
        return [
            [f"{path[i]}_to_{path[i+1]}" for i in range(len(path) - 1)] for path in sorted_paths
        ]
    except nx.NetworkXNoPath as err:
        raise ValueError(f"No conversion path available between {source} and {target}.") from err

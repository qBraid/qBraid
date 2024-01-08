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
from importlib import import_module
from typing import List, Optional

import networkx as nx

from qbraid.interface.conversion_edge import ConversionEdge
from qbraid.transpiler import conversion_functions


class ConversionGraph:
    """
    Class for coordinating conversions between different quantum software programs

    """

    def __init__(self, conversions: Optional[List[ConversionEdge]] = None):
        """
        Initialize a ConversionGraph instance.

        Args:
            conversions (optional, List[ConversionEdge]): List of conversion edges. If None, default
                                                          conversion edges are created.
        """
        self._edges = conversions or self.load_default_conversions()
        self._nx_graph = self.create_conversion_graph()

    @staticmethod
    def load_default_conversions() -> List[ConversionEdge]:
        """
        Create a list of default conversion nodes using predefined conversion functions.

        Returns:
            List[ConversionEdge]: List of default conversion edges.
        """
        transpiler = import_module("qbraid.transpiler")
        return [
            ConversionEdge(*conversion.split("_to_"), getattr(transpiler, conversion))
            for conversion in conversion_functions
        ]

    @property
    def edges(self) -> List[ConversionEdge]:
        """
        Get the list of conversion edges.

        Returns:
            List[ConversionEdge]: The conversion edges of the graph.
        """
        return self._edges

    @property
    def nx_graph(self) -> nx.DiGraph:
        """
        Gets conversion graph.

        Returns:
            nx.DiGraph: The conversion graph.
        """
        return self._nx_graph

    @property
    def nx_nodes(self) -> List[nx.classes.reportviews.NodeView]:
        """
        Retrieve the nodes of the conversion graph.

        This property returns the nodes present in the graph. Each node typically
        represents a quantum package supported by the conversion graph.

        Returns:
            List[nx.classes.reportviews.NodeView]: A list of nodes in the graph, each represented
                                                   as a NodeView object from NetworkX.
        """
        return self._nx_graph.nodes

    @property
    def nx_edges(self) -> List[nx.classes.reportviews.OutEdgeView]:
        """
        Retrieve the edges of the conversion graph.

        This property returns the edges present in the graph. Each edge represents a conversion
        path between two quantum packages.

        Returns:
            List[nx.classes.reportviews.OutEdgeView]: A list of edges in the graph, each represented
                                                      as an OutEdgeView object from NetworkX.
        """
        return self._nx_graph.edges

    def create_conversion_graph(self) -> nx.DiGraph:
        """
        Create a directed graph from a list of conversion functions.

        Args:
            conversion_nodes (optional, List[ConversionEdge]): List of custom conversion nodes.

        Returns:
            nx.DiGraph: The directed graph created from conversion functions.
        """
        graph = nx.DiGraph()
        for edge in self._edges:
            graph.add_edge(edge.source, edge.target, func=edge.convert)
        return graph

    def add_conversion(self, edge: ConversionEdge, overwrite: bool = False) -> None:
        """
        Add a new conversion function as an edge in the graph.

        Args:
            edge (qbraid.interface.ConversionEdge): The conversion edge to add to the graph.
            overwrite (optional, bool): If True, overwrites an existing conversion.
                                        Defaults to False.

        Raises:
            ValueError: If the conversion already exists and overwrite_existing is False.
        """
        source, target = edge.source, edge.target

        if self._nx_graph.has_edge(source, target) and not overwrite:
            raise ValueError(
                f"Conversion from {source} to {target} already exists. "
                "Set overwrite=True to overwrite."
            )

        for old_edge in self._edges:
            if old_edge == edge:
                self._edges.remove(old_edge)
                self._edges.append(edge)

        self._nx_graph.add_edge(source, target, func=edge.convert)

    def find_shortest_conversion_path(self, source: str, target: str) -> List[str]:
        """
        Find the shortest conversion path between two nodes in a graph.

        Args:
            source (str): The starting node for the path.
            target (str): The target node for the path.

        Returns:
            list of str: The shortest conversion path as a list of step strings.

        Raises:
            ValueError: If no path is found between source and target.
        """
        try:
            path = nx.shortest_path(self._nx_graph, source, target)
            return [self._nx_graph[path[i]][path[i + 1]]["func"] for i in range(len(path) - 1)]
        except nx.NetworkXNoPath as err:
            raise ValueError(
                f"No conversion path available between {source} and {target}."
            ) from err

    def find_top_shortest_conversion_paths(
        self, source: str, target: str, top_n: int = 3
    ) -> List[List[str]]:
        """
        Find the top shortest conversion paths between two nodes in a graph.

        Args:
            source (str): The starting node for the path.
            target (str): The target node for the path.
            top_n (int): Number of top shortest paths to find.

        Returns:
            list of list of str: The top shortest conversion paths.

        Raises:
            ValueError: If no path is found between source and target.
        """
        try:
            all_paths = list(nx.all_simple_paths(self._nx_graph, source, target))
            sorted_paths = sorted(all_paths, key=len)[:top_n]
            return [
                [self._nx_graph[path[i]][path[i + 1]]["func"] for i in range(len(path) - 1)]
                for path in sorted_paths
            ]
        except nx.NetworkXNoPath as err:
            raise ValueError(
                f"No conversion path available between {source} and {target}."
            ) from err

    def has_path(self, source: str, target: str) -> bool:
        """
        Check if a conversion between two languages is supported.

        Args:
            source (str): The source language.
            target (str): The target language.

        Returns:
            bool: True if the conversion is supported, False otherwise.
        """
        return nx.has_path(self._nx_graph, source, target)

    def plot_conversion_graph(self) -> None:
        """
        Plot the conversion graph using matplotlib.

        Returns:
            None
        """
        # pylint: disable=import-outside-toplevel

        try:
            import matplotlib.pyplot as plt
        except ImportError as err:
            raise ImportError("Matplotlib is required for plotting the conversion graph.") from err

        graph = self._nx_graph
        pos = nx.spring_layout(graph, seed=123)
        nx.draw_networkx_nodes(graph, pos, node_color="lightblue", node_size=1200)
        nx.draw_networkx_edges(graph, pos, edge_color="gray", min_target_margin=18)
        nx.draw_networkx_labels(graph, pos)
        plt.title("qBraid Quantum Program Conversion Graph")
        plt.axis("off")
        plt.show()

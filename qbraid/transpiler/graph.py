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
Module providing tools to map, analyze, and visualize conversion paths between different
quantum programs available through the qbraid.transpiler using directed graphs.

"""
from importlib import import_module
from typing import Callable, Optional

import rustworkx as rx

from .conversions import conversion_functions
from .edge import Conversion
from .exceptions import ConversionPathNotFoundError


class ConversionGraph(rx.PyDiGraph):
    """
    Class for coordinating conversions between different quantum software programs

    """

    # avoid passing arguments to rx.PyDiGraph.__new__() when inheriting
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)  # pylint: disable=no-value-for-parameter

    def __init__(
        self, conversions: Optional[list[Conversion]] = None, require_native: bool = False
    ):
        """
        Initialize a ConversionGraph instance.

        Args:
            conversions (optional, list[Conversion]): List of conversion edges. If None,
                                                      default conversion edges are used.
            require_native (bool): If True, only include "native" conversion functions.
                                   Defaults to False.
        """
        super().__init__()
        self.require_native = require_native
        self._conversions = conversions or self.load_default_conversions()
        self._node_str_to_id = {}
        self.create_conversion_graph()

    @staticmethod
    def load_default_conversions() -> list[Conversion]:
        """
        Create a list of default conversion nodes using predefined conversion functions.

        Returns:
            list[Conversion]: List of default conversion edges.
        """
        transpiler = import_module("qbraid.transpiler.conversions")
        return [
            Conversion(*conversion.split("_to_"), getattr(transpiler, conversion))
            for conversion in conversion_functions
        ]

    def create_conversion_graph(self) -> None:
        """
        Create a directed graph from a list of conversion functions.

        Returns:
            None
        """
        for edge in (
            e for e in self._conversions if e.supported and (not self.require_native or e.native)
        ):
            if edge.source not in self._node_str_to_id:
                self._node_str_to_id[edge.source] = self.add_node(edge.source)
            if edge.target not in self._node_str_to_id:
                self._node_str_to_id[edge.target] = self.add_node(edge.target)
            self.add_edge(
                self._node_str_to_id[edge.source],
                self._node_str_to_id[edge.target],
                {"native": edge.native, "func": edge.convert},
            )

    def has_node(self, node: str) -> bool:
        """
        Check if a node exists in the graph.

        Args:
            node (str): The node to check.

        Returns:
            bool: True if the node exists, False otherwise.
        """
        return node in self._node_str_to_id

    def has_edge(self, node_a: str, node_b: str) -> bool:
        """
        Check if an edge exists between two nodes in the graph.

        Args:
            node_a (str): The source node.
            node_b (str): The target node.

        Returns:
            bool: True if the edge exists, False otherwise.
        """
        if node_a not in self._node_str_to_id or node_b not in self._node_str_to_id:
            return False  # To avoid KeyError
        return super().has_edge(self._node_str_to_id[node_a], self._node_str_to_id[node_b])

    def conversions(self) -> list[Conversion]:
        """
        Get the list of conversion edges.

        Returns:
            list[Conversion]: The conversion edges of the graph.
        """
        return self._conversions

    def add_conversion(self, edge: Conversion, overwrite: bool = False) -> None:
        """
        Add a new conversion function as an edge in the graph.

        Args:
            edge (qbraid.interface.Conversion): The conversion edge to add to the graph.
            overwrite (optional, bool): If True, overwrites an existing conversion.
                                        Defaults to False.

        Raises:
            ValueError: If the conversion already exists and overwrite_existing is False.
        """
        source, target = edge.source, edge.target

        if self.has_edge(source, target) and not overwrite:
            raise ValueError(
                f"Conversion from {source} to {target} already exists. "
                "Set overwrite=True to overwrite."
            )

        for old_edge in self._conversions:
            if old_edge.source == source and old_edge.target == target:
                self._conversions.remove(old_edge)
                self.remove_edge(
                    self._node_str_to_id[source],
                    self._node_str_to_id[target],
                )
                break

        self._conversions.append(edge)

        if source not in self._node_str_to_id:
            self._node_str_to_id[source] = self.add_node(source)
        if target not in self._node_str_to_id:
            self._node_str_to_id[target] = self.add_node(target)
        self.add_edge(
            self._node_str_to_id[source],
            self._node_str_to_id[target],
            {"native": edge.native, "func": edge.convert},
        )

    def remove_conversion(self, source: str, target: str) -> None:
        """Safely remove a conversion from the graph."""
        if self.has_edge(source, target):
            self.remove_edge(self._node_str_to_id[source], self._node_str_to_id[target])
        else:
            raise ValueError(f"Conversion from {source} to {target} does not exist.")

        self._conversions = [
            conv
            for conv in self._conversions.copy()
            if not (conv.source == source and conv.target == target)
        ]

    def find_shortest_conversion_path(self, source: str, target: str) -> list[Callable]:
        """
        Find the shortest conversion path between two nodes in a graph.

        Args:
            source (str): The starting node for the path.
            target (str): The target node for the path.

        Returns:
            list of Callable: The shortest conversion path
                              as a list of bound methods of Conversion instances.

        Raises:
            ValueError: If no path is found between source and target.
        """
        path = rx.dijkstra_shortest_paths(
            self, self._node_str_to_id[source], target=self._node_str_to_id[target]
        )
        # rx.dijkstra_shortest_paths returns an empty mapping if no path is found
        if len(path) == 0:
            raise ConversionPathNotFoundError(source, target)
        return [
            self.get_edge_data(
                path[self._node_str_to_id[target]][i], path[self._node_str_to_id[target]][i + 1]
            )["func"]
            for i in range(len(path[self._node_str_to_id[target]]) - 1)
        ]

    def find_top_shortest_conversion_paths(
        self, source: str, target: str, top_n: int = 3
    ) -> list[list[Callable]]:
        """
        Find the top shortest conversion paths between two nodes in a graph.

        Args:
            source (str): The starting node for the path.
            target (str): The target node for the path.
            top_n (int): Number of top shortest paths to find.

        Returns:
            list of list of Callable: The top shortest conversion paths.

        Raises:
            ValueError: If no path is found between source and target.
        """
        all_paths = rx.all_simple_paths(
            self, self._node_str_to_id[source], self._node_str_to_id[target]
        )
        # rx.all_simple_paths returns an empty list if no path is found
        if len(all_paths) == 0:
            raise ConversionPathNotFoundError(source, target)
        sorted_paths = sorted(all_paths, key=len)[:top_n]
        return [
            [self.get_edge_data(path[i], path[i + 1])["func"] for i in range(len(path) - 1)]
            for path in sorted_paths
        ]

    def has_path(self, source: str, target: str) -> bool:
        """
        Check if a conversion between two languages is supported.

        Args:
            source (str): The source language.
            target (str): The target language.

        Returns:
            bool: True if the conversion is supported, False otherwise.
        """
        if source == target:
            return True  # nx.has_path returns True, but rx.has_path returns False
        return rx.has_path(self, self._node_str_to_id[source], self._node_str_to_id[target])

    def reset(self, conversions: Optional[list[Conversion]] = None) -> None:
        """
        Reset the graph to its default state.

        Returns:
            None
        """
        self.clear()
        self._conversions = conversions or self.load_default_conversions()
        self._node_str_to_id = {}
        self.create_conversion_graph()

    def plot(self, **kwargs):
        """
        Plot the conversion graph.

        Args:
            **kwargs: Keyword arguments for the plot function.

        Returns:
            None
        """
        # pylint: disable-next=import-outside-toplevel
        from qbraid.visualization.plot_conversions import plot_conversion_graph

        plot_conversion_graph(self, **kwargs)

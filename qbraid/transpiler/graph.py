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

from .conversions import conversion_functions
from .edge import Conversion
from .exceptions import ConversionPathNotFoundError


class ConversionGraph(nx.DiGraph):
    """
    Class for coordinating conversions between different quantum software programs

    """

    def __init__(self, conversions: Optional[List[Conversion]] = None):
        """
        Initialize a ConversionGraph instance.

        Args:
            conversions (optional, List[Conversion]): List of conversion edges. If None, default
                                                          conversion edges are created.
        """
        super().__init__()
        self._conversions = conversions or self.load_default_conversions()
        self.create_conversion_graph()

    @staticmethod
    def load_default_conversions() -> List[Conversion]:
        """
        Create a list of default conversion nodes using predefined conversion functions.

        Returns:
            List[Conversion]: List of default conversion edges.
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
        for edge in self._conversions:
            self.add_edge(edge.source, edge.target, native=edge.native, func=edge.convert)

    def conversions(self) -> List[Conversion]:
        """
        Get the list of conversion edges.

        Returns:
            List[Conversion]: The conversion edges of the graph.
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
                break

        self._conversions.append(edge)
        self.add_edge(source, target, native=edge.native, func=edge.convert)

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
            path = nx.shortest_path(self, source, target)
            return [self[path[i]][path[i + 1]]["func"] for i in range(len(path) - 1)]
        except nx.NetworkXNoPath as err:
            raise ConversionPathNotFoundError(source, target) from err

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
            all_paths = list(nx.all_simple_paths(self, source, target))
            sorted_paths = sorted(all_paths, key=len)[:top_n]
            return [
                [self[path[i]][path[i + 1]]["func"] for i in range(len(path) - 1)]
                for path in sorted_paths
            ]
        except nx.NetworkXNoPath as err:
            raise ConversionPathNotFoundError(source, target) from err

    def has_path(self, source: str, target: str) -> bool:
        """
        Check if a conversion between two languages is supported.

        Args:
            source (str): The source language.
            target (str): The target language.

        Returns:
            bool: True if the conversion is supported, False otherwise.
        """
        return nx.has_path(self, source, target)

    def reset(self, conversions: Optional[List[Conversion]] = None) -> None:
        """
        Reset the graph to its default state.

        Returns:
            None
        """
        self.clear()
        self._conversions = conversions or self.load_default_conversions()
        self.create_conversion_graph()

    def plot(self, **kwargs):
        """
        Plot the conversion graph.

        Args:
            **kwargs: Keyword arguments for the plot function.

        Returns:
            None
        """
        # pylint: disable=import-outside-toplevel
        from qbraid.visualization.plot_conversions import plot_conversion_graph

        plot_conversion_graph(self, **kwargs)

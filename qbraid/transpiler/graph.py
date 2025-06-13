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
from collections import deque
from importlib import import_module
from typing import Any, Callable, Optional, Union

import rustworkx as rx

from qbraid.programs.experiment import ExperimentType
from qbraid.programs.registry import (
    QPROGRAM_ALIASES,
    get_native_experiment_type,
    is_registered_alias_native,
)

from .edge import Conversion
from .exceptions import ConversionPathNotFoundError


def _get_path_from_bound_methods(bound_methods: list[Callable[..., Any]]) -> str:
    """
    Constructs a path string from a list of bound methods of Conversion instances.

    This function takes a list of bound methods (specifically 'convert' methods bound to
    Conversion instances) and constructs a path string representing the sequence of
    conversions. Each conversion is defined by the 'source' and 'target' properties of the
    Conversion instance to which each method is bound.

    Args:
        bound_methods: A list of bound methods from Conversion instances.

    Returns:
        A string representing the path of conversions, formatted as
        'source1 -> source2 -> ... -> targetN'.

    Raises:
        AttributeError: If the bound methods do not have the expected 'source'
                        and 'target' attributes.
        IndexError: If the list of bound methods is empty.
        TypeError: If an item in the bound_methods list is not a bound method.
    """
    if not bound_methods:
        raise IndexError("The list of bound methods is empty.")

    total_methods = len(bound_methods)

    path = []
    for index, method in enumerate(bound_methods):
        instance: Conversion = method.__self__  # Get the instance to which the method is bound
        if not hasattr(instance, "source") or not hasattr(instance, "target"):
            raise AttributeError("Bound method instance lacks 'source' or 'target' attributes.")
        path.append(instance.source)  # Add the source node of the instance

        # Add the target of the last method's instance to complete the path
        if index == total_methods - 1:
            path.append(instance.target)

    return " -> ".join(path)


def parse_conversion_path(conv_repr: str) -> list[tuple[str, str]]:
    """Parse a conversion path string into a list of conversion tuples."""
    components = conv_repr.split(" -> ")
    conversions = []
    for i in range(len(components) - 1):
        conversions.append((components[i], components[i + 1]))
    return conversions


# pylint: disable-next=too-many-public-methods
class ConversionGraph(rx.PyDiGraph):
    """
    Class for coordinating conversions between different quantum software programs

    """

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        return super().__new__(cls)  # pylint: disable=no-value-for-parameter

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        conversions: Optional[list[Conversion]] = None,
        require_native: bool = False,
        include_isolated: bool = True,
        edge_bias: Optional[float] = None,
        nodes: Optional[Union[list[str], set[str]]] = None,
    ):
        """
        Initialize a ConversionGraph instance.

        Args:
            conversions (list[Conversion], optional): List of conversion edges. If None,
                default conversion edges are used.
            require_native (bool): If True, only include "native" conversion functions.
                Defaults to False.
            include_isolated (bool): If True, includes all registered program type aliases, even
                those that are not connected to any other nodes in the graph. Defaults to True.
            edge_bias (float, optional): Factor used to fine-tune the edge weight calculations
                and modify the decision thresholds for pathfinding. Defaults to 0.25 to prioritize
                shorter paths. For example, a bias of 0.25 slightly favors a single conversion at
                weight 0.78 over two conversions at weight 1.0. Only used if conversions is None.
            nodes (list[str], optional): List of nodes to include in the graph. If nodes is None
                and conversions is None, all nodes connected by registered conversions are included.
                If nodes is None and conversions is specified, only nodes connected by the specified
                conversions are included. Isolated nodes included iff include_isolated is True.

        """
        super().__init__()
        self.require_native = require_native
        self.edge_bias = edge_bias if edge_bias is not None else 0.25
        self._conversions = conversions or self.load_default_conversions(bias=self.edge_bias)
        self._node_alias_id_map: dict[str, int] = {}
        self._include_isolated = include_isolated
        self._init_nodes = set(nodes) if nodes is not None else set()
        self.create_conversion_graph()

    @staticmethod
    def load_default_conversions(bias: Optional[float] = None) -> list[Conversion]:
        """
        Create a list of default conversion nodes using predefined conversion functions.

        Returns:
            list[Conversion]: List of default conversion edges.
        """
        transpiler = import_module("qbraid.transpiler.conversions")
        conversion_functions: list[str] = getattr(transpiler, "conversion_functions", [])
        conversion_pairs: list[list[str, str]] = [
            conversion.split("_to_") for conversion in conversion_functions
        ]
        registered_conversion_pairs: list[list[str, str]] = [
            [source, target]
            for source, target in conversion_pairs
            if source in QPROGRAM_ALIASES and target in QPROGRAM_ALIASES
        ]

        def construct_conversion(name: list[str, str]) -> Conversion:
            source, target = name
            conversion_func = getattr(transpiler, f"{source}_to_{target}")
            return Conversion(source, target, conversion_func, bias=bias)

        return [construct_conversion(conversion) for conversion in registered_conversion_pairs]

    def create_conversion_graph(self) -> None:
        """Create a directed graph from a list of conversion functions."""
        nodes = self._init_nodes or set()

        for edge in (
            e for e in self._conversions if e.supported and (not self.require_native or e.native)
        ):
            if nodes and (edge.source not in nodes or edge.target not in nodes):
                continue
            if edge.source not in self._node_alias_id_map:
                self._node_alias_id_map[edge.source] = self.add_node(edge.source)
            if edge.target not in self._node_alias_id_map:
                self._node_alias_id_map[edge.target] = self.add_node(edge.target)
            self.add_edge(
                self._node_alias_id_map[edge.source],
                self._node_alias_id_map[edge.target],
                {"native": edge.native, "func": edge.convert, "weight": edge.weight},
            )

        if self._include_isolated:
            nodes = nodes or QPROGRAM_ALIASES
            for alias in nodes:
                if alias not in self._node_alias_id_map and (
                    not self.require_native or is_registered_alias_native(alias)
                ):
                    self._node_alias_id_map[alias] = self.add_node(alias)

    def has_node(self, node: str) -> bool:
        """
        Check if a node exists in the graph.

        Args:
            node (str): The node to check.

        Returns:
            bool: True if the node exists, False otherwise.
        """
        return node in set(self.nodes())

    def has_edge(self, node_a: str, node_b: str) -> bool:
        """
        Check if an edge exists between two nodes in the graph.

        Args:
            node_a (str): The source node.
            node_b (str): The target node.

        Returns:
            bool: True if the edge exists, False otherwise.
        """
        if not self.has_node(node_a) or not self.has_node(node_b):
            return False

        return super().has_edge(self._node_alias_id_map[node_a], self._node_alias_id_map[node_b])

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
                    self._node_alias_id_map[source],
                    self._node_alias_id_map[target],
                )
                break

        self._conversions.append(edge)

        if source not in self._node_alias_id_map:
            self._node_alias_id_map[source] = self.add_node(source)
        if target not in self._node_alias_id_map:
            self._node_alias_id_map[target] = self.add_node(target)
        self.add_edge(
            self._node_alias_id_map[source],
            self._node_alias_id_map[target],
            {"native": edge.native, "func": edge.convert, "weight": edge.weight},
        )

    def remove_conversion(self, source: str, target: str) -> None:
        """Safely remove a conversion from the graph."""
        if self.has_edge(source, target):
            self.remove_edge(self._node_alias_id_map[source], self._node_alias_id_map[target])
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
            self,
            self._node_alias_id_map[source],
            target=self._node_alias_id_map[target],
            weight_fn=lambda edge: edge["weight"],
        )

        if len(path) == 0:
            raise ConversionPathNotFoundError(source, target)

        return [
            self.get_edge_data(
                path[self._node_alias_id_map[target]][i],
                path[self._node_alias_id_map[target]][i + 1],
            )["func"]
            for i in range(len(path[self._node_alias_id_map[target]]) - 1)
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
            ConversionPathNotFoundError: If no path is found between source and target.
        """
        all_paths = rx.all_simple_paths(
            self, self._node_alias_id_map[source], self._node_alias_id_map[target]
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
            return True

        source_node = self._node_alias_id_map.get(source)
        target_node = self._node_alias_id_map.get(target)

        if source_node is None or target_node is None:
            return False

        return rx.has_path(self, source_node, target_node)

    def shortest_path(self, source: str, target: str) -> str:
        """
        Return string representation of the shortest conversion path between two nodes.

        Args:
            source (str): The starting node for the path.
            target (str): The target node for the path.

        Returns:
            str: String representation of shortest conversion path.

        Raises:
            ConversionPathNotFoundError: If no path is found between source and target.
        """
        path = self.find_shortest_conversion_path(source, target)
        return _get_path_from_bound_methods(path)

    def all_paths(self, source: str, target: str) -> list[str]:
        """
        Return string representations of all conversion paths between two nodes.

        Args:
            source (str): The starting node for the path.
            target (str): The target node for the path.

        Returns:
            list[str]: String representations of all conversion paths.

        Raises:
            ConversionPathNotFoundError: If no path is found between source and target.
        """
        num_conversions = len(self.conversions())
        paths = self.find_top_shortest_conversion_paths(source, target, top_n=num_conversions)
        return [_get_path_from_bound_methods(path) for path in paths]

    @staticmethod
    def _calculate_depth_and_weight(
        path: str, conv_weights: dict[tuple[str, str], int]
    ) -> tuple[int, int]:
        """Calculate the depth and weight of a given path."""
        conv_nodes = path.split(" -> ")
        conv_pairs = list(zip(conv_nodes, conv_nodes[1:]))
        depth = len(conv_pairs)
        weight = sum(conv_weights.get(pair, 0) for pair in conv_pairs)
        return depth, weight

    def _find_closest(
        self,
        pivot: str,
        candidates: list[str],
        has_path_func: Callable[[str, str], Optional[str]],
        shortest_path_func: Callable[[str, str], str],
    ) -> Optional[str]:
        """Find the closest item in candidates to/from pivot based on conversion paths."""
        closest = None
        min_depth = float("inf")
        min_weight = float("inf")

        conv_weights = {(conv.source, conv.target): conv.weight for conv in self.conversions()}

        for candidate in candidates:
            if has_path_func(pivot, candidate):
                path = shortest_path_func(pivot, candidate)
                depth, weight = self._calculate_depth_and_weight(path, conv_weights)

                if (depth < min_depth) or (depth == min_depth and weight < min_weight):
                    min_depth = depth
                    min_weight = weight
                    closest = candidate

        return closest

    def closest_target(self, source: str, targets: list[str]) -> Optional[str]:
        """
        Determine the closest target from a list of possible targets based on the
        shortest conversion path and weights. In case of equal path depths, the
        target with the higher total weight of its path edges is chosen.

        Args:
            source (str): The alias from which conversion paths are evaluated.
            targets (list[str]): A list of target aliases to which the conversion paths
                are evaluated.

        Returns:
            Optional[str]: The name of the target that requires the fewest conversions
                from the source or has higher weights in tie cases. Returns `None` if no
                conversion paths are available.
        """
        if source in targets:
            return source
        return self._find_closest(source, targets, self.has_path, self.shortest_path)

    def closest_source(self, target: str, sources: list[str]) -> Optional[str]:
        """
        Determine the closest source from a list of possible sources based on the
        shortest conversion path and weights. In case of equal path depths, the
        source with the higher total weight of its path edges is chosen.

        Args:
            target (str): The alias to which conversion paths are evaluated.
            sources (list[str]): A list of source aliases from which the conversion paths
                are evaluated.

        Returns:
            Optional[str]: The name of the source that requires the fewest conversions
                to the target or has higher weights in tie cases. Returns `None` if no
                conversion paths are available.
        """
        if target in sources:
            return target
        return self._find_closest(
            target,
            sources,
            lambda tgt, src: self.has_path(src, tgt),
            lambda tgt, src: self.shortest_path(src, tgt),
        )

    @staticmethod
    def _get_sorted_closest(
        pivot: str, items: list[str], closest_func: Callable[[str, list[str]], Optional[str]]
    ) -> list[str]:
        """Sort a list of items from closest to least close based on conversion paths."""
        sorted_items = []
        remaining = items.copy()

        while remaining:
            closest = closest_func(pivot, remaining)
            if closest is None:
                sorted_items.extend(remaining)
                break
            sorted_items.append(closest)
            remaining.remove(closest)

        return sorted_items

    def get_sorted_closest_targets(self, source: str, targets: list[str]) -> list[str]:
        """
        Sorts a list of targets from closest to least close based on conversion paths
        from the source. Targets without valid conversion paths are appended at the end.

        Args:
            source (str): The alias from which conversion paths are evaluated.
            targets (list[str]): A list of target aliases to be ordered by proximity.

        Returns:
            list[str]: A list of target aliases ordered by proximity to the source,
                    with unreachable targets appended at the end.
        """
        return self._get_sorted_closest(source, targets, self.closest_target)

    def get_sorted_closest_sources(self, target: str, sources: list[str]) -> list[str]:
        """
        Sorts a list of sources from closest to least close based on conversion paths
        from the target. Sources without valid conversion paths are appended at the end.

        Args:
            target (str): The alias to which conversion paths are evaluated.
            sources (list[str]): A list of source aliases to be ordered by proximity.

        Returns:
            list[str]: A list of source aliases ordered by proximity to the target,
                    with unreachable sources appended at the end.
        """
        return self._get_sorted_closest(target, sources, self.closest_source)

    def get_node_experiment_types(self) -> dict[str, ExperimentType]:
        """
        Get the experiment type of each node in the graph.

        Returns:
            dict[str, ExperimentType]: A dictionary mapping each node to its experiment type.
        """
        node_to_experiment_type = {}
        unassigned_nodes = deque()

        for node in self.nodes():
            if is_registered_alias_native(node):
                node_to_experiment_type[node] = get_native_experiment_type(node)
            else:
                node_to_experiment_type[node] = None
                unassigned_nodes.append(node)

        while unassigned_nodes:
            node = unassigned_nodes.popleft()
            assigned = False

            for recorded_node, recorded_exp_type in node_to_experiment_type.items():
                if recorded_exp_type is None or recorded_node is None:
                    continue

                if self.has_path(recorded_node, node) or self.has_path(node, recorded_node):
                    if node_to_experiment_type[node] is None:
                        node_to_experiment_type[node] = recorded_exp_type
                        assigned = True
                    elif node_to_experiment_type[node] != recorded_exp_type:
                        raise ValueError(
                            f"ExperimentType conflict detected: Node '{node}' "
                            f"(type '{node_to_experiment_type[node].name}') "
                            f"is reachable from node '{recorded_node}' "
                            f"(type '{recorded_exp_type.name}'), which has a different experiment "
                            "type. Ensure that connected nodes share compatible experiment types."
                        )

            if not assigned:
                node_to_experiment_type[node] = ExperimentType.OTHER

        return node_to_experiment_type

    def reset(self, conversions: Optional[list[Conversion]] = None) -> None:
        """
        Reset the graph to its default state.

        Returns:
            None
        """
        self.clear()
        self._conversions = conversions or self.load_default_conversions()
        self._node_alias_id_map = {}
        self.create_conversion_graph()

    def copy(self):
        """
        Create a copy of this graph, returning a new instance of ConversionGraph.

        """
        copied_conversions = self._conversions.copy() if self._conversions is not None else None
        return ConversionGraph(
            conversions=copied_conversions,
            require_native=self.require_native,
            include_isolated=self._include_isolated,
            edge_bias=self.edge_bias,
            nodes=self._init_nodes,
        )

    def subgraph(
        self, experiment_type: Union[ExperimentType, list[ExperimentType]]
    ) -> "ConversionGraph":
        """Filter the graph to include only nodes with the specified experiment type(s).

        Args:
            experiment_type (Union[ExperimentType, list[ExperimentType]]): The experiment type(s)

        Returns:
            ConversionGraph: A new ConversionGraph instance with only nodes of the
                specified experiment type(s).

        Raises:
            ValueError: If there are no nodes with the specified experiment type(s) in the graph.
        """
        node_experiment_types = self.get_node_experiment_types()
        exp_types = experiment_type if isinstance(experiment_type, list) else [experiment_type]
        nodes = [n for n in self.nodes() if node_experiment_types[n] in exp_types]

        if not nodes:
            exp_type_names = ", ".join([exp_type.name for exp_type in exp_types])
            raise ValueError(
                f"No program type nodes found with experiment type(s) '{exp_type_names}'. "
                "Use ConversionGraph.get_node_experiment_types() to inspect all experiment "
                "type mappings in this graph."
            )

        self._init_nodes = set(nodes)

        return self.copy()

    def __eq__(self, value: object) -> bool:
        return (
            super().__eq__(value)
            and isinstance(value, ConversionGraph)
            and self.conversions() == value.conversions()
            and self.require_native == value.require_native
            and self._node_alias_id_map == value._node_alias_id_map
            and self._include_isolated == value._include_isolated
            and self.edge_bias == value.edge_bias
            and self._init_nodes == value._init_nodes
        )

    def plot(self, **kwargs):
        """
        Plot the conversion graph.

        .. note::

            Matplotlib is an optional dependency and will not be installed with
            qbraid by default. If you intend to use this method make sure that
            you install matplotlib with either ``pip install matplotlib`` or
            ``pip install 'qbraid[visualization]'``.

        Args:
            **kwargs: Keyword arguments for the plot function.

        Returns:
            None
        """
        # pylint: disable-next=import-outside-toplevel
        from qbraid.visualization.plot_conversions import plot_conversion_graph

        plot_conversion_graph(self, **kwargs)

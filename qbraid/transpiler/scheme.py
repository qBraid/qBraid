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
Module for managing conversion configurations for quantum runtime.

"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.programs.spec import ProgramSpec

from .graph import ConversionGraph, parse_conversion_path

if TYPE_CHECKING:
    import rustworkx as rx


@dataclass
class ConversionScheme:
    """
    A data class for managing conversion configurations for quantum device operations.

    Attributes:
        conversion_graph (Optional[ConversionGraph]): Graph coordinating conversions between
            different quantum software program types. If None, the default qBraid graph is used.
        max_path_attempts (int): The maximum number of conversion paths to attempt before
            raising an exception. Defaults to 3.
        max_path_depth (Optional[int]): The maximum depth of conversions within a given path to
            allow. A depth of 2 would allow a conversion path like ['cirq' -> 'qasm2' -> 'qiskit'].
            Defaults to None, meaning no limit.
        extra_kwargs (dict[str, Any]): A dictionary to hold any additional keyword arguments that
            users want to pass to the transpile function at runtime.

    Methods:
        to_dict: Converts the conversion scheme to a flat dictionary suitable for passing as kwargs.
        update_values: Dynamically updates the values of the instance's attributes.
    """

    conversion_graph: Optional[ConversionGraph] = None
    max_path_attempts: int = 3
    max_path_depth: Optional[int] = None
    extra_kwargs: dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        kwargs_str = ", ".join(f"{key}={value}" for key, value in self.extra_kwargs.items())
        return (
            f"ConversionScheme(conversion_graph={self.conversion_graph}, "
            f"max_path_attempts={self.max_path_attempts}, "
            f"max_path_depth={self.max_path_depth}, "
            f"{kwargs_str})"
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the ConversionScheme fields to a flat dictionary suitable for passing as kwargs.

        Returns:
            A dictionary with all fields ready to be passed as keyword arguments,
            including nested extra_kwargs.
        """
        scheme = asdict(self)
        scheme.update(scheme.pop("extra_kwargs", {}))
        scheme.update({"conversion_graph": self.conversion_graph})
        return scheme

    def update_values(self, **kwargs) -> None:
        """
        Updates the attributes of the conversion scheme with new values provided
        as keyword arguments.

        Args:
            **kwargs: Arbitrary keyword arguments containing attribute names and their new values.

        Raises:
            AttributeError: If a provided attribute name does not exist.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"{key} is not a valid attribute of ConversionScheme")

    @staticmethod
    def find_nodes_reachable_within_max_edges(
        graph: rx.PyDiGraph,
        target_nodes: Union[list[str], set[str]],
        max_edges: Optional[int] = None,
    ) -> set[str]:
        """Find all nodes reachable from a target node within a specified number of edges.

        Args:
            graph (rx.PyDiGraph): The graph to search.
            target_nodes (list[str]): The target nodes from which to search.
            max_edges (int, optional): The maximum number of edges to traverse.

        Returns:
            set[str]: The set of nodes reachable from the target nodes within the specified
                number of edges.

        Raises:
            ValueError: If the target node is not found in the graph,
                or if the maximum number of edges is negative.
        """
        if max_edges is None:
            max_edges = graph.num_edges()
        elif max_edges < 0:
            raise ValueError("The maximum number of edges must be a non-negative integer.")

        graph_nodes = graph.nodes()
        node_to_index = {node: i for i, node in enumerate(graph_nodes)}
        target_indices = set()

        for target_node in set(target_nodes):
            if target_node not in node_to_index:
                raise ValueError(f"Target node '{target_node}' not found in the graph.")
            target_indices.add(node_to_index[target_node])

        reachable_nodes = set(target_indices)

        for _ in range(max_edges):
            new_nodes = set()
            for node in reachable_nodes:
                preds = graph.predecessors(node)
                preds_indices = [node_to_index[pred] for pred in preds]
                new_nodes.update(preds_indices)
            if not new_nodes.difference(reachable_nodes):
                break
            reachable_nodes.update(new_nodes)

        return {graph_nodes[i] for i in reachable_nodes}

    @staticmethod
    def prune_graph_to_target_paths(
        graph: ConversionGraph, target_nodes: list[str], n_steps: Optional[int]
    ) -> ConversionGraph:
        """
        Prune edges that do not contribute to paths within n steps of any of the target nodes.

        Args:
            graph (ConversionGraph): The graph to prune
            target_nodes (List[str]): The list of node indices to center the pruning around
            n_steps (int): Number of steps to consider from each target node

        Returns:
            ConversionGraph: The pruned graph
        """
        graph = graph.copy()

        all_nodes: set[str] = set(graph.nodes())
        target_set: set[str] = set(target_nodes)
        sources: set[str] = all_nodes - target_set
        all_used_paths: set[tuple[str, str]] = set()

        # Collect all paths within n_steps for each target node
        for target_node in target_nodes:
            for source in sources:
                if graph.has_path(source, target_node):
                    for path_str in graph.all_paths(source, target_node):
                        path_tuple_lst = parse_conversion_path(path_str)
                        if n_steps is None or len(path_tuple_lst) <= n_steps:
                            all_used_paths.update(path_tuple_lst)

        # Create a mapping from node IDs to aliases
        node_id_to_alias = {value: key for key, value in graph._node_alias_id_map.items()}

        # Prune edges not in used paths
        for edge in graph.edge_list():
            src_node_id, target_node_id = edge
            src_node_alias = node_id_to_alias[src_node_id]
            target_node_alias = node_id_to_alias[target_node_id]

            if (src_node_alias, target_node_alias) not in all_used_paths:
                graph.remove_conversion(src_node_alias, target_node_alias)

        return graph

    def reset_graph(self, include_isolated: bool = True) -> None:
        """Reset the conversion graph to the default qBraid graph."""
        self.update_values(conversion_graph=ConversionGraph(include_isolated=include_isolated))

    def update_graph_for_target(self, target_spec: Union[ProgramSpec, list[ProgramSpec]]) -> None:
        """Update the conversion graph to include only nodes with paths to the target node(s), and
        remove all conversions that do not end in the target node(s)."""
        graph = (
            self.conversion_graph.copy()
            if self.conversion_graph
            else ConversionGraph(include_isolated=True)
        )

        target_nodes = {
            spec.alias for spec in (target_spec if isinstance(target_spec, list) else [target_spec])
        }

        nodes = self.find_nodes_reachable_within_max_edges(graph, target_nodes, self.max_path_depth)

        conversions = [conv for conv in graph.conversions() if conv.source not in target_nodes]

        updated_graph = ConversionGraph(
            conversions=conversions,
            require_native=graph.require_native,
            include_isolated=graph._include_isolated,
            edge_bias=graph.edge_bias,
            nodes=nodes,
        )

        pruned_graph = self.prune_graph_to_target_paths(
            updated_graph, target_nodes, self.max_path_depth
        )

        self.update_values(conversion_graph=pruned_graph)

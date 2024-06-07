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
Module for transpiling quantum programs between different quantum programming languages

"""
import logging
import warnings
from copy import deepcopy
from typing import TYPE_CHECKING, Callable, Optional

from qbraid.programs import QPROGRAM_ALIASES, ProgramTypeError, get_program_type_alias

from .exceptions import CircuitConversionError, ConversionPathNotFoundError, NodeNotFoundError
from .graph import ConversionGraph

if TYPE_CHECKING:
    import qbraid.programs


logger = logging.getLogger(__name__)


def _warn_if_unsupported(program_type, program_direction):
    if program_type not in QPROGRAM_ALIASES:
        warnings.warn(
            f"Converting {program_direction} unsupported program type '{program_type}'.",
            UserWarning,
        )


def _format_exception(err: Exception) -> str:
    return f"{type(err).__name__}: {str(err)}\n"


def _get_path_from_bound_methods(bound_methods: list[Callable]) -> str:
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
    """
    if not bound_methods:
        raise IndexError("The list of bound methods is empty.")

    path = []
    for method in bound_methods:
        instance = method.__self__  # Get the instance to which the method is bound
        if not hasattr(instance, "source") or not hasattr(instance, "target"):
            raise AttributeError("Bound method instance lacks 'source' or 'target' attributes.")
        path.append(instance.source)  # Add the source node of the instance

    # Add the target of the last method's instance to complete the path
    path.append(bound_methods[-1].__self__.target)

    return " -> ".join(path)


def transpile(
    program: "qbraid.programs.QPROGRAM",
    target: str,
    conversion_graph: Optional[ConversionGraph] = None,
    max_path_attempts: int = 3,
    max_path_depth: Optional[int] = None,
    **kwargs,
) -> "qbraid.programs.QPROGRAM":
    """
    Transpile a quantum program to a target language using a conversion graph.
    This function attempts to find a conversion path from the program's current
    format to the target format. It can limit the search to a certain number of
    attempts and path depths.

    Args:
        program (qbraid.programs.QPROGRAM): The quantum program to transpile.
        target (str): The target language to transpile to.
        conversion_graph (Optional[ConversionGraph]): The graph representing available conversions.
            If None, a default graph is used. Defaults to None.
        max_path_attempts (int): The maximum number of conversion paths to attempt before raising an
            exception. This is useful to avoid excessive computations when multiple paths are
            available. Defaults to 3.
        max_path_depth (Optional[int]): The maximum depth of conversions within a given path to
            allow. For example, a path with a depth of 2 would be ['cirq' -> 'qasm2' -> 'qiskit'],
            whereas a depth  of 1 would be a direct conversion ['cirq' -> 'braket']. Defaults
            to None, i.e. no limit set on the path depth.

    Returns:
        qbraid.programs.QPROGRAM: The transpiled quantum program.

    Raises:
        NodeNotFoundError: If the target or source package is not in the ConversionGraph.
        ConversionPathNotFoundError: If no path is available to conversion between the
            source and target packages.
        CircuitConversionError: If the conversion fails through all attempted paths.
    """
    graph = conversion_graph or ConversionGraph(**kwargs)
    graph_type = "Default" if conversion_graph is None else "Provided"

    if not graph.has_node(target):
        raise NodeNotFoundError(graph_type, target, graph.nodes())

    source = get_program_type_alias(program)

    if not graph.has_node(source):
        raise NodeNotFoundError(graph_type, source, graph.nodes())

    if not graph.has_path(source, target):
        raise ConversionPathNotFoundError(source, target)

    if source == target:
        return program

    _warn_if_unsupported(source, "from")
    _warn_if_unsupported(target, "to")

    paths = graph.find_top_shortest_conversion_paths(source, target, top_n=max_path_attempts)

    if max_path_depth is not None:
        paths = [path for path in paths if len(path) <= max_path_depth]
        if len(paths) == 0:
            raise ConversionPathNotFoundError(source, target, max_path_depth)

    error_messages = []

    for path in paths:
        path_details = _get_path_from_bound_methods(path)
        temp_program = deepcopy(program)
        try:
            for convert_func in path:
                try:
                    temp_program = convert_func(temp_program)
                except Exception as err:  # pylint: disable=broad-exception-caught
                    try:
                        alias = get_program_type_alias(temp_program)
                    except ProgramTypeError:
                        alias = None

                    if alias == "cirq":
                        # pylint: disable=import-outside-toplevel
                        from qbraid.transforms.cirq import decompose

                        temp_program = decompose(temp_program)
                        temp_program = convert_func(temp_program)  # Retry conversion
                    else:
                        error_detail = (
                            f"Conversion {path_details} failed due to "
                            f"exception raised while converting from '{alias}'."
                        )
                        error_messages.append(error_detail)
                        error_messages.append(_format_exception(err))
                        raise

            logger.info("\nSuccessfully transpiled using conversions: %s", path_details)
            return temp_program
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.info("\nFailed to transpile using conversions: %s", path_details)
            formatted_error = _format_exception(err)
            if len(error_messages) == 0 or error_messages[-1] != formatted_error:
                error_messages.append(formatted_error)
            continue

    raise CircuitConversionError(
        f"Failed to convert '{source}' to '{target}'"
        + (
            " due to the following error(s):\n\n" + "\n".join(error_messages)
            if error_messages
            else "."
        )
    )

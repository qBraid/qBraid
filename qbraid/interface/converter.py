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
Module for transpiling quantum programs between different quantum programming languages

"""
import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Callable, List, Optional

from qbraid._qprogram import QPROGRAM_LIBS
from qbraid.exceptions import PackageValueError
from qbraid.interface.conversion_graph import ConversionGraph
from qbraid.interface.inspector import get_program_type
from qbraid.transpiler import CircuitConversionError

if TYPE_CHECKING:
    import cirq

    import qbraid


def _flatten_cirq(circuit: "cirq.Circuit") -> "cirq.Circuit":
    """
    Flatten a Cirq circuit.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to flatten.

    Returns:
        cirq.Circuit: The flattened Cirq circuit.
    """
    # TODO: potentially replace with native cirq.decompose
    # https://quantumai.google/reference/python/cirq/decompose

    # pylint: disable=import-outside-toplevel
    from cirq.contrib.qasm_import import circuit_from_qasm

    return circuit_from_qasm(circuit.to_qasm())


def _get_path_from_bound_methods(bound_methods: List[Callable]) -> str:
    """
    Constructs a path string from a list of bound methods of ConversionEdge instances.

    This function takes a list of bound methods (specifically 'convert' methods bound to
    ConversionEdge instances) and constructs a path string representing the sequence of
    conversions. Each conversion is defined by the 'source' and 'target' properties of the
    ConversionEdge instance to which each method is bound.

    Args:
        bound_methods: A list of bound methods from ConversionEdge instances.

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


def convert_to_package(
    program: "qbraid.QPROGRAM", target: str, conversion_graph: Optional[ConversionGraph] = None
) -> "qbraid.QPROGRAM":
    """
    Transpile a quantum program to a target language.

    Args:
        program (qbraid.QPROGRAM): The quantum program to transpile.
        target (str): The target language to transpile to.

    Returns:
        qbraid.QPROGRAM: The transpiled quantum program.
    """
    if target not in QPROGRAM_LIBS:
        raise PackageValueError(target)

    source = get_program_type(program)

    if source == target:
        return program

    graph = conversion_graph or ConversionGraph()

    if not graph.has_path(source, target):
        raise CircuitConversionError(f"No conversion path available from {source} to {target}.")

    paths = graph.find_top_shortest_conversion_paths(source, target, top_n=3)

    for path in paths:
        temp_program = deepcopy(program)
        try:
            for convert_func in path:
                try:
                    temp_program = convert_func(temp_program)
                except Exception:  # pylint: disable=broad-exception-caught
                    if get_program_type(temp_program) == "cirq":
                        temp_program = _flatten_cirq(temp_program)
                        temp_program = convert_func(temp_program)  # Retry conversion
                    else:
                        raise
            logging.info(
                "\n\nSuccessfully transpiled using conversions: %s",
                _get_path_from_bound_methods(path),
            )
            return temp_program
        except Exception:  # pylint: disable=broad-exception-caught
            continue

    raise CircuitConversionError(f"Failed to transpile program from {source} to {target}.")

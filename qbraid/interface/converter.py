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
from importlib import import_module
from typing import TYPE_CHECKING, List

from qbraid._qprogram import QPROGRAM_LIBS
from qbraid.exceptions import PackageValueError, ProgramTypeError, QasmError
from qbraid.interface.qasm_checks import get_qasm_version
from qbraid.transpiler import CircuitConversionError, conversion_functions

from .conversion_graph import create_conversion_graph, find_top_shortest_conversion_paths

if TYPE_CHECKING:
    import cirq

    import qbraid

transpiler = import_module("qbraid.transpiler")


def _flatten_cirq(circuit: "cirq.Circuit") -> "cirq.Circuit":
    """
    Flatten a Cirq circuit.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to flatten.

    Returns:
        cirq.Circuit: The flattened Cirq circuit.
    """
    # pylint: disable=import-outside-toplevel
    from cirq.contrib.qasm_import import circuit_from_qasm

    return circuit_from_qasm(circuit.to_qasm())


def _get_program_type(program: "qbraid.QPROGRAM") -> str:
    """
    Get the type of a quantum program.

    Args:
        program (qbraid.QPROGRAM): The quantum program to get the type of.

    Returns:
        str: The type of the quantum program.
    """
    if isinstance(program, str):
        try:
            package = get_qasm_version(program)
        except QasmError as err:
            raise ProgramTypeError(
                "Input of type string must represent a valid OpenQASM program."
            ) from err

    else:
        try:
            program_module = program.__module__
            package = program_module.split(".")[0].lower()
        except AttributeError as err:
            raise ProgramTypeError(program) from err

    if package not in QPROGRAM_LIBS:
        raise PackageValueError(package)

    return package


def _convert_path_to_string(path: List[str]) -> str:
    """
    Convert a conversion path to a string of package names.

    Args:
        path (list): The conversion path.

    Returns:
        str: A string representing the sequence of packages in the path.
    """
    conversion_packages = [path[0].split("_to_")[0]] + [
        conversion.split("_to_")[1] for conversion in path
    ]
    return " -> ".join(conversion_packages)


def convert_to_package(program: "qbraid.QPROGRAM", target: str) -> "qbraid.QPROGRAM":
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

    source = _get_program_type(program)

    if source == target:
        return program

    graph = create_conversion_graph(conversion_functions)
    paths = find_top_shortest_conversion_paths(graph, source, target)

    for path in paths:
        logging.info("Conversion paths: %s", _convert_path_to_string(path))
        # print(_convert_path_to_string(path))

    for path in paths:
        temp_program = deepcopy(program)
        try:
            for conversion in path:
                try:
                    convert_func = getattr(transpiler, conversion)
                    temp_program = convert_func(temp_program)
                except Exception:  # pylint: disable=broad-exception-caught
                    if _get_program_type(temp_program) == "cirq":
                        temp_program = _flatten_cirq(temp_program)
                        temp_program = convert_func(temp_program)  # Retry conversion
                    else:
                        raise
            logging.info(
                "\n\nSuccessfully transpiled using conversions: %s", _convert_path_to_string(path)
            )
            return temp_program
        except Exception:  # pylint: disable=broad-exception-caught
            continue

    raise CircuitConversionError(f"Failed to transpile program from {source} to {target}.")

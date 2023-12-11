# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=import-outside-toplevel

"""
Module containing functions for converting to/from OpenQASM 3 circuit representation.

"""
from typing import TYPE_CHECKING

from openqasm3 import parse as openqasm_parse

from qbraid.exceptions import PackageValueError, ProgramTypeError, QasmError
from qbraid.qasm_checks import get_qasm_version
from qbraid.transpiler.exceptions import CircuitConversionError

if TYPE_CHECKING:
    import qbraid


def convert_to_qasm3(program: "qbraid.QPROGRAM") -> str:
    """Converts any valid input quantum program to an OpenQASM 3 program.

    Args:
        program (:data:`~qbraid.QPROGRAM`): A qbraid-supported quantum program object.

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        CircuitConversionError: If the input quantum program could not be converted.

    Returns:
        str: OpenQASM 3 program.
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
            package = program.__module__
        except AttributeError as err:
            raise ProgramTypeError(program) from err

    # pylint: disable=import-outside-toplevel

    try:
        if "qiskit" in package:
            from qbraid.transpiler.qiskit.conversions_qasm import qiskit_to_qasm3

            return qiskit_to_qasm3(program)

        if "braket" in package:
            from qbraid.transpiler.braket.conversions_qasm import braket_to_qasm3

            return braket_to_qasm3(program)

        if "openqasm3" in package:
            from openqasm3 import dumps

            return dumps(program)

        if package == "qasm2":
            from qbraid.transpiler.qasm.convert_qasm import qasm2_to_qasm3

            return qasm2_to_qasm3(program)

        if package == "qasm3":
            return program

    except Exception as err:
        raise CircuitConversionError(
            "Quantum program could not be converted to an OpenQASM 3."
        ) from err

    raise ProgramTypeError(program)


def convert_from_qasm3(program: str, frontend: str) -> "qbraid.QPROGRAM":
    """Converts an OpenQASM 3 string to a type specified by the conversion type.

    Args:
        program: OpenQASM 3 string to convert.
        frontend: String specifier for the converted circuit type.

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        CircuitConversionError: If the input quantum program could not be converted.

    Returns:
        :data:`~qbraid.QPROGRAM`: A ``conversion_type`` quantum circuit / program.
    """
    # pylint: disable=import-outside-toplevel

    try:
        if frontend == "qiskit":
            from qbraid.transpiler.qiskit.conversions_qasm import qasm3_to_qiskit

            return qasm3_to_qiskit(program)

        if frontend == "braket":
            from qbraid.transpiler.braket.conversions_qasm import qasm3_to_braket

            return qasm3_to_braket(program)

        if frontend == "openqasm3":
            return openqasm_parse(program)

        if frontend == "qasm3":
            return program

    except Exception as err:
        raise CircuitConversionError(
            f"OpenQASM 3 program could not be converted to a quantum program of type {frontend}."
        ) from err

    raise PackageValueError(frontend)

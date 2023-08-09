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
Module containing functions for converting to/from Cirq's circuit representation.

"""
from typing import TYPE_CHECKING, Tuple

from cirq import Circuit
from cirq.contrib.qasm_import import circuit_from_qasm
from qiskit.qasm3 import loads as qiskit_from_qasm3

from qbraid.exceptions import PackageValueError, ProgramTypeError
from qbraid.interface.qbraid_qasm.tools import convert_to_qasm3
from qbraid.transpiler.cirq_braket import from_braket, to_braket
from qbraid.transpiler.cirq_pyquil import from_pyquil, to_pyquil
from qbraid.transpiler.cirq_pytket import from_pytket, to_pytket
from qbraid.transpiler.cirq_qasm import from_qasm, to_qasm
from qbraid.transpiler.cirq_qiskit import from_qiskit, to_qiskit
from qbraid.transpiler.exceptions import CircuitConversionError, QasmError
from qbraid.transpiler.qasm_checks import get_qasm_version

if TYPE_CHECKING:
    import qbraid


def convert_to_cirq(program: "qbraid.QPROGRAM") -> Tuple[Circuit, str]:
    """Converts any valid input quantum program to a Cirq circuit.

    Args:
        program (:data:`~qbraid.QPROGRAM`): A qbraid-supported quantum program object.

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        CircuitConversionError: If the input quantum program could not be converted.

    Returns:
        A Tuple containing the Cirq circuit equivalent to input circuit and the
            input quantum program type.
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

    try:
        if "qiskit" in package:
            return from_qiskit(program), "qiskit"

        if "pyquil" in package:
            return from_pyquil(program), "pyquil"

        if "braket" in package:
            return from_braket(program), "braket"

        if "pytket" in package:
            return from_pytket(program), "pytket"

        if package == "qasm2":
            return from_qasm(program), package

        if package == "qasm3":
            qiskit_circuit = qiskit_from_qasm3(program)
            return from_qiskit(qiskit_circuit), package

        if isinstance(program, Circuit):
            return program, "cirq"

    except Exception as err:
        raise CircuitConversionError(
            "Quantum program could not be converted to a Cirq circuit."
        ) from err

    raise ProgramTypeError(program)


def _convert_from_cirq(circuit: Circuit, frontend: str) -> "qbraid.QPROGRAM":
    """Converts a Cirq circuit to a type specified by the conversion type.

    Args:
        circuit: Cirq circuit to convert.
        frontend: String specifier for the converted circuit type.

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        CircuitConversionError: If the input quantum program could not be converted.

    Returns:
        :data:`~qbraid.QPROGRAM`: A ``conversion_type`` quantum circuit / program.
    """
    try:
        if frontend == "qiskit":
            return to_qiskit(circuit)

        if frontend == "pyquil":
            return to_pyquil(circuit)

        if frontend == "braket":
            return to_braket(circuit)

        if frontend == "pytket":
            return to_pytket(circuit)

        if frontend == "qasm2":
            return to_qasm(circuit)

        if frontend == "qasm3":
            qasm2_str = to_qasm(circuit)
            return convert_to_qasm3(qasm2_str)

        if frontend == "cirq":
            return circuit

    except Exception as err:
        raise CircuitConversionError(
            f"Cirq Circuit could not be converted to a " f"quantum program of type {frontend}."
        ) from err

    raise PackageValueError(frontend)


def convert_from_cirq(circuit: Circuit, frontend: str) -> "qbraid.QPROGRAM":
    """Converts a Cirq circuit to a type specified by the conversion type.

    Args:
        circuit: Cirq circuit to convert.
        frontend: String specifier for the converted circuit type.

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        CircuitConversionError: If the input quantum program could not be converted.

    Returns:
        :data:`~qbraid.QPROGRAM`: A ``conversion_type`` quantum circuit / program.
    """
    try:
        return _convert_from_cirq(circuit, frontend)
    except CircuitConversionError:
        circuit_flat = circuit_from_qasm(circuit.to_qasm())  # flatten circuit
        return _convert_from_cirq(circuit_flat, frontend)

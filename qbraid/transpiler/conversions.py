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
from openqasm3 import parse as openqasm_parse

from qbraid.exceptions import PackageValueError, ProgramTypeError, QasmError
from qbraid.qasm_checks import get_qasm_version
from qbraid.transpiler.cirq_qasm import from_qasm, to_qasm
from qbraid.transpiler.exceptions import CircuitConversionError

if TYPE_CHECKING:
    import cirq

    import qbraid


def convert_to_cirq(program: "qbraid.QPROGRAM") -> Tuple["cirq.Circuit", str]:
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

    # pylint: disable=import-outside-toplevel

    try:
        if "qiskit" in package:
            from qbraid.transpiler.cirq_qiskit import from_qiskit

            return from_qiskit(program), "qiskit"

        if "pyquil" in package:
            from qbraid.transpiler.cirq_pyquil import from_pyquil

            return from_pyquil(program), "pyquil"

        if "braket" in package:
            from qbraid.transpiler.cirq_braket import from_braket

            return from_braket(program), "braket"

        if "pytket" in package:
            from qbraid.transpiler.cirq_pytket import from_pytket

            return from_pytket(program), "pytket"

        if "openqasm3" in package:
            from openqasm3 import dumps
            from qiskit.qasm3 import loads

            from qbraid.transpiler.cirq_qiskit import from_qiskit

            qasm_str = dumps(program)
            return from_qiskit(loads(qasm_str)), "openqasm3"

        if package == "qasm2":
            return from_qasm(program), package

        if package == "qasm3":
            from qiskit.qasm3 import loads

            from qbraid.transpiler.cirq_qiskit import from_qiskit

            qiskit_circuit = loads(program)
            return from_qiskit(qiskit_circuit), package

        if isinstance(program, Circuit):
            return program, "cirq"

    except Exception as err:
        raise CircuitConversionError(
            "Quantum program could not be converted to a Cirq circuit."
        ) from err

    raise ProgramTypeError(program)


def _convert_from_cirq(circuit: "cirq.Circuit", frontend: str) -> "qbraid.QPROGRAM":
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
    # pylint: disable=import-outside-toplevel

    try:
        if frontend == "qiskit":
            from qbraid.transpiler.cirq_qiskit import to_qiskit

            return to_qiskit(circuit)

        if frontend == "pyquil":
            from qbraid.transpiler.cirq_pyquil import to_pyquil

            try:
                return to_pyquil(circuit)
            except CircuitConversionError:
                cirq_compat = circuit_from_qasm(circuit.to_qasm())
                return to_pyquil(cirq_compat)

        if frontend == "braket":
            from qbraid.transpiler.cirq_braket import to_braket

            return to_braket(circuit)

        if frontend == "pytket":
            from qbraid.transpiler.cirq_pytket import to_pytket

            return to_pytket(circuit)

        if frontend == "qasm2":
            return to_qasm(circuit)

        if frontend == "qasm3":
            from qbraid.interface.qbraid_qasm3.tools import convert_to_qasm3

            qasm2_str = to_qasm(circuit)
            return convert_to_qasm3(qasm2_str)

        if frontend == "openqasm3":
            from qbraid.interface.qbraid_qasm3.tools import convert_to_qasm3

            qasm3_str = convert_to_qasm3(to_qasm(circuit))
            return openqasm_parse(qasm3_str)

        if frontend == "cirq":
            return circuit

    except Exception as err:
        raise CircuitConversionError(
            f"Cirq Circuit could not be converted to a " f"quantum program of type {frontend}."
        ) from err

    raise PackageValueError(frontend)


def convert_from_cirq(circuit: "cirq.Circuit", frontend: str) -> "qbraid.QPROGRAM":
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

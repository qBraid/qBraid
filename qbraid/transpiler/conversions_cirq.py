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
from typing import TYPE_CHECKING

from cirq import Circuit
from cirq.contrib.qasm_import import circuit_from_qasm
from openqasm3 import parse as openqasm_parse

from qbraid.exceptions import PackageValueError, ProgramTypeError, QasmError
from qbraid.qasm_checks import get_qasm_version
from qbraid.transpiler.cirq import cirq_to_qasm2, qasm2_to_cirq
from qbraid.transpiler.exceptions import CircuitConversionError

if TYPE_CHECKING:
    import cirq

    import qbraid


def convert_to_cirq(program: "qbraid.QPROGRAM") -> "cirq.Circuit":
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
            from qbraid.transpiler.qiskit import qiskit_to_qasm2

            qasm_str = qiskit_to_qasm2(program)
            return convert_to_cirq(qasm_str)

        if "pyquil" in package:
            from qbraid.transpiler.pyquil import pyquil_to_cirq

            return pyquil_to_cirq(program)

        if "braket" in package:
            from qbraid.transpiler.braket import braket_to_cirq

            return braket_to_cirq(program)

        if "pytket" in package:
            from qbraid.transpiler.pytket import pytket_to_qasm2

            qasm2_str = pytket_to_qasm2(program)
            return convert_to_cirq(qasm2_str)

        if "openqasm3" in package:
            from openqasm3 import dumps

            qasm_str = dumps(program)
            return convert_to_cirq(qasm_str)

        if package == "qasm2":
            return qasm2_to_cirq(program, map_qbraid_circuit=True)

        if package == "qasm3":
            from qbraid.transpiler.qiskit import qasm3_to_qiskit

            qiskit_circuit = qasm3_to_qiskit(program)
            return convert_to_cirq(qiskit_circuit)

        if isinstance(program, Circuit):
            return program

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
            from qbraid.transpiler.qiskit import qasm2_to_qiskit

            qasm_str = cirq_to_qasm2(circuit, map_qbraid_circuit=True)
            return qasm2_to_qiskit(qasm_str)

        if frontend == "pyquil":
            from qbraid.transpiler.pyquil import cirq_to_pyquil

            return cirq_to_pyquil(circuit)

        if frontend == "braket":
            from qbraid.transpiler.braket import cirq_to_braket

            return cirq_to_braket(circuit)

        if frontend == "pytket":
            from qbraid.transpiler.pytket import qasm2_to_pytket

            qasm2_str = cirq_to_qasm2(circuit)
            return qasm2_to_pytket(qasm2_str)

        if frontend == "qasm2":
            return cirq_to_qasm2(circuit)

        if frontend == "qasm3":
            from qbraid.transpiler.qasm.convert_qasm import qasm2_to_qasm3

            qasm2_str = cirq_to_qasm2(circuit)
            return qasm2_to_qasm3(qasm2_str)

        if frontend == "openqasm3":
            from qbraid.transpiler.qasm.convert_qasm import qasm2_to_qasm3

            qasm3_str = qasm2_to_qasm3(cirq_to_qasm2(circuit))
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
        pass

    try:
        circuit_flat = circuit_from_qasm(circuit.to_qasm())  # flatten circuit
        return _convert_from_cirq(circuit_flat, frontend)
    except ValueError as err:
        raise CircuitConversionError(
            f"Cirq Circuit could not be converted to a " f"quantum program of type {frontend}."
        ) from err

# Copyright (C) 2020 Unitary Fund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Module containing functions for converting to/from Cirq's circuit representation.

"""
from typing import TYPE_CHECKING, Any, Callable, Tuple

from cirq import Circuit

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import PackageValueError, ProgramTypeError
from qbraid.transpiler.exceptions import CircuitConversionError

if TYPE_CHECKING:
    import qbraid

# pylint: disable=import-outside-toplevel


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
    conversion_function: Callable[[Any], Circuit]

    try:
        package = program.__module__
    except AttributeError as err:
        raise ProgramTypeError(program) from err

    if "qiskit" in package:
        from qbraid.transpiler.cirq_qiskit import from_qiskit

        input_program_type = "qiskit"
        conversion_function = from_qiskit
    elif "pyquil" in package:
        from qbraid.transpiler.cirq_pyquil import from_pyquil

        input_program_type = "pyquil"
        conversion_function = from_pyquil
    elif "braket" in package:
        from qbraid.transpiler.cirq_braket import from_braket

        input_program_type = "braket"
        conversion_function = from_braket
    elif "pennylane" in package:
        from qbraid.transpiler.cirq_pennylane import from_pennylane

        input_program_type = "pennylane"
        conversion_function = from_pennylane
    elif isinstance(program, Circuit):
        input_program_type = "cirq"

        def conversion_function(circ: Circuit) -> Circuit:
            return circ

    else:
        raise ProgramTypeError(program)

    try:
        cirq_circuit = conversion_function(program)
    except Exception as err:
        raise CircuitConversionError(
            "Quantum program could not be converted to a Cirq circuit. "
            "This may be because the circuit contains custom gates or "
            f"Pragmas (pyQuil). \n\nProvided program has type {type(program)} "
            f"and is:\n\n{program}\n\nQuantum program types supported by the "
            f"qbraid.transpiler are \n{SUPPORTED_PROGRAM_TYPES}."
        ) from err

    return cirq_circuit, input_program_type


def convert_from_cirq(circuit: Circuit, conversion_type: str) -> "qbraid.QPROGRAM":
    """Converts a Cirq circuit to a type specified by the conversion type.

    Args:
        circuit: Cirq circuit to convert.
        conversion_type: String specifier for the converted circuit type.

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        CircuitConversionError: If the input quantum program could not be converted.

    Returns:
        :data:`~qbraid.QPROGRAM`: A ``conversion_type`` quantum circuit / program.
    """
    conversion_function: Callable[[Circuit], QPROGRAM]
    if conversion_type == "qiskit":
        from qbraid.transpiler.cirq_qiskit import to_qiskit

        conversion_function = to_qiskit
    elif conversion_type == "pyquil":
        from qbraid.transpiler.cirq_pyquil import to_pyquil

        conversion_function = to_pyquil
    elif conversion_type == "braket":
        from qbraid.transpiler.cirq_braket import to_braket

        conversion_function = to_braket
    elif conversion_type == "pennylane":
        from qbraid.transpiler.cirq_pennylane import to_pennylane

        conversion_function = to_pennylane
    elif conversion_type == "cirq":

        def conversion_function(circ: Circuit) -> Circuit:
            return circ

    else:
        raise PackageValueError(conversion_type)

    try:
        quantum_program = conversion_function(circuit)
    except Exception as err:
        raise CircuitConversionError(
            f"Cirq Circuit could not be converted to a "
            f"quantum program of type {conversion_type}."
        ) from err

    return quantum_program

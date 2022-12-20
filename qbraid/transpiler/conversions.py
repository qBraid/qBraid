# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=import-outside-toplevel

"""
Module containing functions for converting to/from Cirq's circuit representation.

"""
from typing import TYPE_CHECKING, Tuple

from cirq import Circuit

from qbraid.exceptions import PackageValueError, ProgramTypeError
from qbraid.transpiler.cirq_braket import from_braket, to_braket
from qbraid.transpiler.cirq_pyquil import from_pyquil, to_pyquil
from qbraid.transpiler.cirq_qiskit import from_qiskit, to_qiskit
from qbraid.transpiler.exceptions import CircuitConversionError

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

        if isinstance(program, Circuit):
            return program, "cirq"

    except Exception as err:
        raise CircuitConversionError(
            "Quantum program could not be converted to a Cirq circuit."
        ) from err

    raise ProgramTypeError(program)


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
        if frontend == "qiskit":
            return to_qiskit(circuit)

        if frontend == "pyquil":
            return to_pyquil(circuit)

        if frontend == "braket":
            return to_braket(circuit)

        if frontend == "cirq":
            return circuit

    except Exception as err:
        raise CircuitConversionError(
            f"Cirq Circuit could not be converted to a " f"quantum program of type {frontend}."
        ) from err

    raise PackageValueError(frontend)

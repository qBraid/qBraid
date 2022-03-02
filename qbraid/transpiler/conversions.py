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

"""Functions for converting to/from Cirq's circuit representation."""
from typing import Any, Callable, Tuple

from cirq import Circuit

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import UnsupportedCircuitError
from qbraid.transpiler.exceptions import CircuitConversionError


def convert_to_cirq(circuit: QPROGRAM) -> Tuple[Circuit, str]:
    """Converts any valid input circuit to a Cirq circuit.

    Args:
        circuit: Any quantum circuit object supported by qbraid.transpiler.
                 See qbraid.transpiler.SUPPORTED_PROGRAM_TYPES.

    Raises:
        UnsupportedCircuitError: If the input circuit is not supported.

    Returns:
        circuit: Cirq circuit equivalent to input circuit.
        input_circuit_type: Type of input circuit represented by a string.
    """
    conversion_function: Callable[[Any], Circuit]

    try:
        package = circuit.__module__
    except AttributeError:
        raise UnsupportedCircuitError("Could not determine the package of the input circuit.")

    if "qiskit" in package:
        from qbraid.transpiler.cirq_qiskit import from_qiskit

        input_circuit_type = "qiskit"
        conversion_function = from_qiskit
    elif "pyquil" in package:
        from qbraid.transpiler.cirq_pyquil import from_pyquil

        input_circuit_type = "pyquil"
        conversion_function = from_pyquil
    elif "braket" in package:
        from qbraid.transpiler.cirq_braket import from_braket

        input_circuit_type = "braket"
        conversion_function = from_braket
    elif "pennylane" in package:
        from qbraid.transpiler.cirq_pennylane import from_pennylane

        input_circuit_type = "pennylane"
        conversion_function = from_pennylane
    elif isinstance(circuit, Circuit):
        input_circuit_type = "cirq"

        def conversion_function(circ: Circuit) -> Circuit:
            return circ

    else:
        raise UnsupportedCircuitError(
            f"Circuit from module {package} is not supported.\n\n"
            "Circuit types supported by the qbraid.transpiler are"
            f"\n{SUPPORTED_PROGRAM_TYPES}"
        )

    try:
        cirq_circuit = conversion_function(circuit)
    except Exception:
        raise CircuitConversionError(
            "Circuit could not be converted to a Cirq circuit. "
            "This may be because the circuit contains custom gates or "
            f"Pragmas (pyQuil). \n\nProvided circuit has type {type(circuit)} "
            f"and is:\n\n{circuit}\n\nCircuit types supported by the "
            f"qbraid.transpiler are \n{SUPPORTED_PROGRAM_TYPES}."
        )

    return cirq_circuit, input_circuit_type


def convert_from_cirq(circuit: Circuit, conversion_type: str) -> QPROGRAM:
    """Converts a Cirq circuit to a type specified by the conversion type.

    Args:
        circuit: Cirq circuit to convert.
        conversion_type: String specifier for the converted circuit type.
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
        raise UnsupportedCircuitError(
            f"Conversion to circuit of type {conversion_type} is "
            "unsupported. \nCircuit types supported by the "
            f"qbraid.transpiler = {SUPPORTED_PROGRAM_TYPES}"
        )
    try:
        converted_circuit = conversion_function(circuit)
    except Exception:
        raise CircuitConversionError(
            f"Circuit could not be converted from a Cirq type to a "
            f"circuit of type {conversion_type}."
        )

    return converted_circuit

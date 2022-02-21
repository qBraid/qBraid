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
from functools import wraps
from typing import Any, Callable, Iterable, Tuple, cast

from black import err
from cirq import Circuit

from qbraid.transpiler2._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES


class UnsupportedCircuitError(Exception):
    pass


class CircuitConversionError(Exception):
    pass


def convert_to_cirq(circuit: QPROGRAM) -> Tuple[Circuit, str]:
    """Converts any valid input circuit to a Cirq circuit.

    Args:
        circuit: Any quantum circuit object supported by qbraid.transpiler2.
                 See qbraid.transpiler2.SUPPORTED_PROGRAM_TYPES.

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
        from qbraid.transpiler2.interface.qiskit.conversions import from_qiskit

        input_circuit_type = "qiskit"
        conversion_function = from_qiskit
    elif "pyquil" in package:
        from qbraid.transpiler2.interface.pyquil.conversions import from_pyquil

        input_circuit_type = "pyquil"
        conversion_function = from_pyquil
    elif "braket" in package:
        from qbraid.transpiler2.interface.braket.convert_from_braket import from_braket

        input_circuit_type = "braket"
        conversion_function = from_braket
    elif "pennylane" in package:
        from qbraid.transpiler2.interface.pennylane.conversions import from_pennylane

        input_circuit_type = "pennylane"
        conversion_function = from_pennylane
    elif isinstance(circuit, Circuit):
        input_circuit_type = "cirq"

        def conversion_function(circ: Circuit) -> Circuit:
            return circ

    else:
        raise UnsupportedCircuitError(
            f"Circuit from module {package} is not supported.\n\n"
            "Circuit types supported by the qbraid.transpiler2 are"
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
            f"qbraid.transpiler2 are \n{SUPPORTED_PROGRAM_TYPES}."
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
        from qbraid.transpiler2.interface.qiskit.conversions import to_qiskit

        conversion_function = to_qiskit
    elif conversion_type == "pyquil":
        from qbraid.transpiler2.interface.pyquil.conversions import to_pyquil

        conversion_function = to_pyquil
    elif conversion_type == "braket":
        from qbraid.transpiler2.interface.braket.convert_to_braket import to_braket

        conversion_function = to_braket
    elif conversion_type == "pennylane":
        from qbraid.transpiler2.interface.pennylane.conversions import to_pennylane

        conversion_function = to_pennylane
    elif conversion_type == "cirq":

        def conversion_function(circ: Circuit) -> Circuit:
            return circ

    else:
        raise UnsupportedCircuitError(
            f"Conversion to circuit of type {conversion_type} is "
            "unsupported. \nCircuit types supported by the "
            f"qbraid.transpiler2 = {SUPPORTED_PROGRAM_TYPES}"
        )
    converted_circuit = conversion_function(circuit)
    # try:
    #     converted_circuit = conversion_function(circuit)
    # except Exception:
    #     raise CircuitConversionError(
    #         f"Circuit could not be converted from a Cirq type to a "
    #         f"circuit of type {conversion_type}."
    #     )

    return converted_circuit


def accept_any_qprogram_as_input(
    accept_cirq_circuit_function: Callable[[Circuit], Any]
) -> Callable[[QPROGRAM], Any]:
    @wraps(accept_cirq_circuit_function)
    def accept_any_qprogram_function(circuit: QPROGRAM, *args: Any, **kwargs: Any) -> Any:
        cirq_circuit, _ = convert_to_cirq(circuit)
        return accept_cirq_circuit_function(cirq_circuit, *args, **kwargs)  # type: ignore

    return accept_any_qprogram_function


def atomic_converter(cirq_circuit_modifier: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator which allows for a function which inputs and returns a Cirq
    circuit to input and return any QPROGRAM.

    Args:
        cirq_circuit_modifier: Function which inputs a Cirq circuit and returns
            a (potentially modified) Cirq circuit.
    """

    @wraps(cirq_circuit_modifier)
    def qprogram_modifier(circuit: QPROGRAM, *args: Any, **kwargs: Any) -> QPROGRAM:
        # Convert to Cirq representation.
        cirq_circuit, input_circuit_type = convert_to_cirq(circuit)

        # Modify the Cirq circuit.
        scaled_circuit = cirq_circuit_modifier(cirq_circuit, *args, **kwargs)

        if kwargs.get("return_cirq") is True:
            return scaled_circuit

        # Base conversion back to input type.
        scaled_circuit = convert_from_cirq(scaled_circuit, input_circuit_type)

        return scaled_circuit

    return qprogram_modifier


def atomic_one_to_many_converter(
    cirq_circuit_modifier: Callable[..., Iterable[Circuit]]
) -> Callable[..., Iterable[QPROGRAM]]:
    @wraps(cirq_circuit_modifier)
    def qprogram_modifier(circuit: QPROGRAM, *args: Any, **kwargs: Any) -> Iterable[QPROGRAM]:
        cirq_circuit, input_circuit_type = convert_to_cirq(circuit)

        modified_circuits: Iterable[Circuit] = cirq_circuit_modifier(cirq_circuit, *args, **kwargs)

        if kwargs.get("return_cirq") is True:
            return modified_circuits

        return [
            convert_from_cirq(modified_circuit, input_circuit_type)
            for modified_circuit in modified_circuits
        ]

    return qprogram_modifier


def noise_scaling_converter(noise_scaling_function: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for handling conversions with noise scaling functions.

    Args:
        noise_scaling_function: Function which inputs a cirq.Circuit, modifies
            it to scale noise, then returns a cirq.Circuit.
    """

    @wraps(noise_scaling_function)
    def new_scaling_function(circuit: QPROGRAM, *args: Any, **kwargs: Any) -> QPROGRAM:
        scaled_circuit = atomic_converter(noise_scaling_function)(circuit, *args, **kwargs)

        # PyQuil: Restore declarations, measurements, and metadata.
        if "pyquil" in scaled_circuit.__module__:
            from pyquil import Program
            from pyquil.quilbase import Declare, Measurement

            circuit = cast(Program, circuit)

            # Grab all measurements from the input circuit.
            measurements = [
                instr for instr in circuit.instructions if isinstance(instr, Measurement)
            ]

            # Remove memory declarations added from Cirq -> pyQuil conversion.
            new_declarations = {
                k: v
                for k, v in scaled_circuit.declarations.items()
                if k == "ro" or v.memory_type != "BIT"
            }
            new_declarations.update(circuit.declarations)

            # Delete all declarations and measurements from the scaled circuit.
            instructions = [
                instr
                for instr in scaled_circuit.instructions
                if not (isinstance(instr, (Declare, Measurement)))
            ]

            # Add back original declarations and measurements.
            scaled_circuit = Program(list(new_declarations.values()) + instructions + measurements)

            # Set the number of shots to the input circuit.
            scaled_circuit.num_shots = circuit.num_shots

        # Qiskit: Keep the same register structure and measurement order.
        if "qiskit" in scaled_circuit.__module__:
            from qbraid.transpiler2.interface.qiskit.conversions import (
                _measurement_order,
                _transform_registers,
            )

            scaled_circuit.remove_final_measurements()
            _transform_registers(
                scaled_circuit,
                new_qregs=circuit.qregs,  # type: ignore
            )
            if circuit.cregs and not scaled_circuit.cregs:  # type: ignore
                scaled_circuit.add_register(*circuit.cregs)  # type: ignore

            for q, c in _measurement_order(circuit):
                scaled_circuit.measure(q, c)

        return scaled_circuit

    return new_scaling_function

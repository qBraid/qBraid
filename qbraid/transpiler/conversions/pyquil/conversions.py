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
Module containing functions to convert between Cirq's circuit
representation and pyQuil's circuit representation (Quil programs).

"""
from cirq import Circuit, LineQubit
from cirq.ops import QubitOrder
from pyquil import Program

from qbraid.transpiler.exceptions import CircuitConversionError

from .quil_input import circuit_from_quil
from .quil_output import QuilOutput


def cirq_to_pyquil(circuit: Circuit) -> Program:
    """Returns a pyQuil Program equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a pyQuil Program.

    Returns:
        pyquil.Program object equivalent to the input Cirq circuit.
    """
    input_qubits = circuit.all_qubits()
    max_qubit = max(input_qubits)
    # if we are using LineQubits, keep the qubit labeling the same
    if isinstance(max_qubit, LineQubit):
        qubit_range = max_qubit.x + 1
        qubit_order = LineQubit.range(qubit_range)
    # otherwise, use the default ordering (starting from zero)
    else:
        qubit_order = QubitOrder.DEFAULT
    qubits = QubitOrder.as_qubit_order(qubit_order).order_for(input_qubits)
    operations = circuit.all_operations()
    try:
        quil_str = str(QuilOutput(operations, qubits))
        return Program(quil_str)
    except ValueError as err:
        raise CircuitConversionError(
            f"Cirq qasm converter doesn't yet support {err.args[0][32:]}."
        ) from err


def pyquil_to_cirq(program: Program) -> Circuit:
    """Returns a Cirq circuit equivalent to the input pyQuil Program.

    Args:
        program: PyQuil Program to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input pyQuil Program.
    """
    try:
        return circuit_from_quil(program.out())
    except Exception as err:
        raise CircuitConversionError(
            "qBraid transpiler doesn't yet support pyQuil noise gates."
        ) from err

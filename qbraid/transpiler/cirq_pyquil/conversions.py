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

from qbraid import circuit_wrapper
from qbraid.transpiler.cirq_pyquil.quil_input import circuit_from_quil
from qbraid.transpiler.cirq_pyquil.quil_output import QuilOutput
from qbraid.transpiler.exceptions import CircuitConversionError


def to_pyquil(circuit: Circuit, compat: bool = True) -> Program:
    """Returns a pyQuil Program equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a pyQuil Program.

    Returns:
        pyquil.Program object equivalent to the input Cirq circuit.
    """
    if compat:
        qprogram = circuit_wrapper(circuit)
        qprogram.convert_to_contiguous()
        circuit = qprogram.program
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


def from_pyquil(program: Program, compat: bool = True) -> Circuit:
    """Returns a Cirq circuit equivalent to the input pyQuil Program.

    Args:
        program: PyQuil Program to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input pyQuil Program.
    """
    try:
        circuit = circuit_from_quil(program.out())
        if compat:
            qprogram = circuit_wrapper(circuit)
            qprogram.convert_to_contiguous()
            circuit = qprogram.program
        return circuit
    except Exception as err:
        raise CircuitConversionError(
            "qBraid transpiler doesn't yet support pyQuil noise gates."
        ) from err

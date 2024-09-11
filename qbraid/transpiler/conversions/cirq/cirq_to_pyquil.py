# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing function to convert from Cirq's circuit
representation to pyQuil's circuit representation (Quil programs).

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from cirq import LineQubit, QubitOrder
from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import CircuitConversionError

try:
    from .cirq_quil_output import QuilOutput
except ImportError:  # pragma: no cover
    QuilOutput = None

pyquil = LazyLoader("pyquil", globals(), "pyquil")

if TYPE_CHECKING:
    import cirq.circuits
    import pyquil as pyquil_


@weight(0.74)
def cirq_to_pyquil(circuit: cirq.circuits.Circuit) -> pyquil_.Program:
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
        return pyquil.Program(quil_str)
    except ValueError as err:
        raise CircuitConversionError(
            f"Cirq qasm converter doesn't yet support {err.args[0][32:]}."
        ) from err

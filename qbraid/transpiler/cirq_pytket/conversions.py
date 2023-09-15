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
representation and pytket's circuit representation.

"""
from cirq import Circuit
from pytket.circuit import Circuit as TKCircuit
from pytket.qasm import circuit_from_qasm_str, circuit_to_qasm_str

from qbraid import circuit_wrapper
from qbraid.transpiler.cirq_qasm import from_qasm, to_qasm
from qbraid.transpiler.custom_gates import _map_zpow_and_unroll
from qbraid.transpiler.exceptions import CircuitConversionError


def to_pytket(circuit: Circuit) -> TKCircuit:
    """Returns a pytket circuit equivalent to the input Cirq circuit. Note
    that the output circuit registers may not match the input circuit
    registers.

    Args:
        circuit: Cirq circuit to convert to a pytket circuit.

    Returns:
        Pytket circuit object equivalent to the input Cirq circuit.
    """
    try:
        qprogram = circuit_wrapper(circuit)
        qprogram.convert_to_contiguous()
        contig_circuit = qprogram.program
        compat_circuit = _map_zpow_and_unroll(contig_circuit)
        return circuit_from_qasm_str(to_qasm(compat_circuit))
    except ValueError as err:
        raise CircuitConversionError("Cirq qasm converter doesn't yet support qasm3.") from err


def from_pytket(circuit: TKCircuit, compat=False) -> Circuit:
    """Returns a Cirq circuit equivalent to the input pytket circuit.

    Args:
        circuit: pytket circuit to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input pytket circuit.
    """
    try:
        qasm_str = circuit_to_qasm_str(circuit)
        cirq_circuit = from_qasm(qasm_str)
        if compat:
            qprogram = circuit_wrapper(cirq_circuit)
            qprogram.convert_to_contiguous()
            cirq_circuit = qprogram.program
        return cirq_circuit
    except Exception as err:
        raise CircuitConversionError("Cirq qasm converter doesn't yet support qasm3.") from err

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
representation and Qiskit's circuit representation.

"""
import cirq
import qiskit

from qbraid import circuit_wrapper
from qbraid.transpiler.cirq_qasm import from_qasm, to_qasm
from qbraid.transpiler.custom_gates import _map_zpow_and_unroll
from qbraid.transpiler.exceptions import CircuitConversionError


def to_qiskit(circuit: cirq.Circuit) -> qiskit.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input Cirq circuit. Note
    that the output circuit registers may not match the input circuit
    registers.

    Args:
        circuit: Cirq circuit to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input Cirq circuit.
    """
    try:
        qprogram = circuit_wrapper(circuit)
        qprogram.convert_to_contiguous()
        contig_circuit = qprogram.program
        compat_circuit = _map_zpow_and_unroll(contig_circuit)
        return qiskit.QuantumCircuit.from_qasm_str(to_qasm(compat_circuit))
    except ValueError as err:
        raise CircuitConversionError from err


def from_qiskit(circuit: qiskit.QuantumCircuit) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input Qiskit circuit.

    Args:
        circuit: Qiskit circuit to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input Qiskit circuit.
    """
    try:
        qasm_str = circuit.qasm()
        cirq_circuit = from_qasm(qasm_str)
        qprogram = circuit_wrapper(cirq_circuit)
        qprogram._convert_to_line_qubits()
        return qprogram.program
    except Exception as err:
        raise CircuitConversionError from err

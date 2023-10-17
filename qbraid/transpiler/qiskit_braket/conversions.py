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
Module containing functions to convert between Qiskit's circuit
representation and Braket's circuit representation via OpenQASM 3.0.
"""
from braket.circuits import Circuit as BraketCircuit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.qasm3 import dumps, loads

from qbraid.interface.qbraid_braket.qasm import braket_from_qasm3, braket_to_qasm3
from qbraid.transpiler.conversions import convert_from_cirq, convert_to_cirq
from qbraid.transpiler.exceptions import CircuitConversionError


def braket_to_qiskit(circuit: BraketCircuit) -> QiskitCircuit:
    """Convert a Braket circuit to a Qiskit circuit.

    Args:
        circuit: Braket circuit to convert.
    Returns:
        Qiskit circuit.
    """
    try:
        qasm3_str = braket_to_qasm3(circuit)
        if "stdgates.inc" not in qasm3_str:
            qasm3_str = qasm3_str.replace(
                "OPENQASM 3.0;\n", 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'
            )
        return loads(qasm3_str)
    except CircuitConversionError as err:
        # pylint: disable=broad-exception-caught
        print("Couldn't convert to Qiskit circuit using Braket's qasm3 converter.")
        print("Exception: ", err)
        print("Fallback to Cirq converter...")
        return convert_from_cirq(convert_to_cirq(circuit)[0], "qiskit")


def qiskit_to_braket(circuit: QiskitCircuit) -> BraketCircuit:
    """Convert a Qiskit circuit to a Braket circuit.

    Args:
        circuit: Qiskit circuit to convert.
    Returns:
        Braket circuit.
    """
    try:
        qasm3_str = dumps(circuit)
        if "stdgates.inc" not in qasm3_str:
            qasm3_str = qasm3_str.replace(
                "OPENQASM 3.0;\n", 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'
            )
        return braket_from_qasm3(qasm3_str)
    except CircuitConversionError as err:
        # pylint: disable=broad-exception-caught
        print("Couldn't convert to Braket circuit using Qiskit's QASM3 converter.")
        print("Exception: ", err)
        print("Fallback to Cirq converter...")
        return convert_from_cirq(convert_to_cirq(circuit)[0], "braket")

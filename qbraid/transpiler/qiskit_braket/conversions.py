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
import warnings

from braket.circuits import Circuit as BraketCircuit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.qasm3 import dumps, loads

from qbraid.transpiler.cirq_braket.braket_qasm import braket_from_qasm3, braket_to_qasm3
from qbraid.transpiler.exceptions import CircuitConversionError

qasm3_header_path = "qbraid/interface/qbraid_qasm3/stdgates.qasm"
with open(qasm3_header_path, "r", encoding="utf-8") as file:
    qasm3_header = file.read()

gates_defs_path = "qbraid/transpiler/qiskit_braket/gate_defs.qasm"
with open(gates_defs_path, "r", encoding="utf-8") as file:
    gate_defs = file.read()


def braket_to_qiskit(circuit: BraketCircuit) -> QiskitCircuit:
    """Convert a Braket circuit to a Qiskit circuit.

    Args:
        circuit: Braket circuit to convert.
    Returns:
        Qiskit circuit.
    """
    try:
        qasm3_str = braket_to_qasm3(circuit)
        qasm3_str = qasm3_str.replace('include "stdgates.inc";\n', "")
        qasm3_str = qasm3_str.replace(
            "OPENQASM 3.0;", f"OPENQASM 3.0;\n{qasm3_header}\n{gate_defs}"
        )

        return loads(qasm3_str)
    except CircuitConversionError as err:
        message = (
            "Couldn't convert to Qiskit circuit using Braket's native OpenQASM 3 converter.\n"
            f"Exception: {err}\n"
            "Fallback to Cirq converter..."
        )
        warnings.warn(message)
        return None


def qiskit_to_braket(circuit: QiskitCircuit) -> BraketCircuit:
    """Convert a Qiskit circuit to a Braket circuit.

    Args:
        circuit: Qiskit circuit to convert.
    Returns:
        Braket circuit.
    """
    try:
        qasm3_str = dumps(circuit)
        qasm3_str = qasm3_str.replace('include "stdgates.inc";\n', "")
        qasm3_str = qasm3_str.replace("OPENQASM 3;", f"OPENQASM 3.0;\n{qasm3_header}\n{gate_defs}")
        return braket_from_qasm3(qasm3_str)
    except CircuitConversionError as err:
        message = (
            "Couldn't convert to Braket circuit using Qiskit's native OpenQASM 3 converter.\n"
            f"Exception: {err}\n"
            "Fallback to Cirq converter..."
        )
        warnings.warn(message)
        return None

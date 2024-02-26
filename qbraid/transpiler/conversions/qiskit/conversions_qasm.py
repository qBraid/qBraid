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
Module defining Qiskit OpenQASM conversions

"""
import qiskit
from qiskit.qasm2 import dumps as qasm2_dumps
from qiskit.qasm3 import QASM3ImporterError, dumps, loads

gate_defs = {
    "iswap": """
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}""",
    "sxdg": """
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}""",
}


def _insert_gate_defs(qasm3_str: str) -> str:
    """Add gate definitions to a QASM 3.0 string.

    Args:
        qasm3_str (str): QASM 3.0 string.
    Returns:
        str: QASM 3.0 string with gate definitions.
    """
    lines = qasm3_str.splitlines()

    insert_index = 0
    for i, line in enumerate(lines):
        if "include" in line or "OPENQASM" in line:
            insert_index = i + 1

    for gate, defn in gate_defs.items():
        if gate in qasm3_str:
            lines.insert(insert_index, defn.strip())

    return "\n".join(lines)


def _add_stdgates_include(qasm_str: str) -> str:
    """Add 'include "stdgates.inc";' to the QASM string if it is missing."""
    if 'include "stdgates.inc";' in qasm_str:
        return qasm_str

    lines = qasm_str.splitlines()

    for i, line in enumerate(lines):
        if "OPENQASM" in line:
            lines.insert(i + 1, 'include "stdgates.inc";')
            break

    return "\n".join(lines)


def qasm3_to_qiskit(qasm3: str) -> qiskit.QuantumCircuit:
    """Convert QASM 3.0 string to a Qiskit QuantumCircuit representation.

    Args:
        qasm3 (str): A string in QASM 3.0 format.

    Returns:
        qiskit.QuantumCircuit: A QuantumCircuit object representing the input QASM 3.0 string.
    """
    # extra trailing space is intentional
    replacements = {
        "cnot ": "cx ",
        "si ": "sdg ",
        "ti ": "tdg ",
        "v ": "sx ",
        "vi ": "sxdg ",
        "phaseshift": "p",
        "cphaseshift": "cp",
    }

    def replace_commands(qasm_str, replacements):
        for old, new in replacements.items():
            qasm_str = qasm_str.replace(old, new)
        return qasm_str

    try:
        return loads(qasm3)
    except QASM3ImporterError:
        pass

    qasm3 = replace_commands(qasm3, replacements)
    qasm3 = _add_stdgates_include(qasm3)
    qasm3 = _insert_gate_defs(qasm3)

    return loads(qasm3)


def qiskit_to_qasm3(circuit: qiskit.QuantumCircuit) -> str:
    """Convert qiskit QuantumCircuit to QASM 3.0 string"""
    return dumps(circuit)


def qasm2_to_qiskit(qasm: str) -> qiskit.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input OpenQASM 2 string.

    Args:
        qasm: OpenQASM 2 string to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input OpenQASM 2 string.
    """
    return qiskit.QuantumCircuit.from_qasm_str(qasm)


def qiskit_to_qasm2(circuit: qiskit.QuantumCircuit) -> str:
    """Returns OpenQASM 2 string equivalent to the input Qiskit circuit.

    Args:
        circuit: Qiskit circuit to convert to OpenQASM 2 string.

    Returns:
        str: OpenQASM 2 representation of the input Qiskit circuit.
    """
    return qasm2_dumps(circuit)

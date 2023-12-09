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

from qiskit import QuantumCircuit
from qiskit.qasm3 import dumps, loads

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


def qiskit_from_qasm3(qasm3_str: str) -> QuantumCircuit:
    """Convert QASM 3.0 string to qiskit QuantumCircuit repr"""
    qasm3_str = qasm3_str.replace("cnot ", "cx ")
    qasm3_str = qasm3_str.replace("si ", "sdg ")
    qasm3_str = qasm3_str.replace("ti ", "tdg ")
    qasm3_str = qasm3_str.replace("v ", "sx ")
    qasm3_str = qasm3_str.replace("vi ", "sxdg ")
    qasm3_str = qasm3_str.replace("phaseshift", "p")
    qasm3_str = qasm3_str.replace("cphaseshift", "cp")
    qasm3_str = _add_stdgates_include(qasm3_str)
    qasm3_str = _insert_gate_defs(qasm3_str)
    return loads(qasm3_str)


def qiskit_to_qasm3(circuit: QuantumCircuit) -> str:
    """Convert qiskit QuantumCircuit to QASM 3.0 string"""
    return dumps(circuit)

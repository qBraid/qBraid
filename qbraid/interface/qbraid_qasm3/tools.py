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
Module containing OpenQASM 3 tools

"""
import os
from typing import List

import numpy as np
from openqasm3.ast import QubitDeclaration
from openqasm3.parser import parse
from qiskit.qasm3 import dumps, loads

from qbraid.interface.qbraid_qiskit.tools import _convert_to_contiguous_qiskit, _unitary_from_qiskit

QASMType = str


def qasm3_qubits(qasmstr: str) -> List[QASMType]:
    """Get number of qasm qubits.

    Args:
        qasmstr (str): OpenQASM 3 string

    Returns:
        List of qubits in the circuit
    """
    program = parse(qasmstr)

    qubits = []
    for statement in program.statements:
        if isinstance(statement, QubitDeclaration):
            qubits.append((statement.qubit.name, statement.size.value))
    return qubits


def qasm3_num_qubits(qasmstr: str) -> int:
    """Calculate number of qubits in a qasm3 string"""
    program = parse(qasmstr)

    num_qubits = 0
    for statement in program.statements:
        if isinstance(statement, QubitDeclaration):
            num_qubits += statement.size.value
    return num_qubits


def qasm3_depth(qasmstr: str) -> int:
    """Calculates circuit depth of OpenQASM 3 string"""
    return loads(qasmstr).depth()


def _unitary_from_qasm3(qasmstr: QASMType) -> np.ndarray:
    """Return the unitary of the QASM 3 string"""
    circuit = loads(qasmstr)
    return _unitary_from_qiskit(circuit)


def _convert_to_contiguous_qasm3(qasmstr: QASMType, rev_qubits=False) -> QASMType:
    """Delete qubit(s) with no gate, if any exist."""
    circuit = loads(qasmstr)
    circuit_contig = _convert_to_contiguous_qiskit(circuit, rev_qubits=rev_qubits)
    return dumps(circuit_contig)


def _build_qasm_3_reg(line: str, qreg_type: bool) -> QASMType:
    """Helper function to build openqasm 3 register statements

    Args:
        line (str): openqasm 2  regdecl statement
        qreg_type (bool): whether a qreg or creg type statement

    Returns:
        str : openqasm 3 qubits / bits declaration
    """
    reg_keyword_len = 4
    line = line[reg_keyword_len:]
    elements = line.split("[")
    reg_name = elements[0].strip()
    reg_size = elements[1].split("]")[0].strip()
    result = "qubit" if qreg_type else "bit"
    result += f"[{reg_size}] {reg_name};\n"
    return result


def _build_qasm_3_measure(line: str) -> QASMType:
    """Helper function to build openqasm 3 measure string

    Args:
        line (str): openqasm 2 measure statement

    Returns:
        str:  openqasm 3 measure statement
    """
    measure_keyword_len = 7
    line = line[measure_keyword_len:]
    elements = line.split("->")
    qubits_name = elements[0].replace(" ", "")
    bits_name = elements[1].split(";")[0].replace(" ", "")

    return f"{bits_name} = measure {qubits_name};\n"


def _change_to_qasm_3(line: str) -> QASMType:
    """Function to change an openqasm 2 line to openqasm 3

    Args:
        line (str): an openqasm 2 line

    Returns:
        str: corresponding openqasm 3 line
    """
    # pylint: disable=import-outside-toplevel
    from qbraid.interface.qbraid_qasm.qelib1_defs import _decompose_rxx_instr

    line = line.lstrip()
    if line.startswith("OPENQASM"):
        return ""
    if "qelib1.inc" in line:
        return ""
    if line.startswith("qreg"):
        return _build_qasm_3_reg(line, qreg_type=True)
    if line.startswith("creg"):
        return _build_qasm_3_reg(line, qreg_type=False)
    if line.startswith("u("):
        return line.replace("u(", "U(")
    if line.startswith("rxx("):
        return _decompose_rxx_instr(line)
    if line.startswith("measure"):
        return _build_qasm_3_measure(line)
    if line.startswith("opaque"):
        # as opaque is ignored by openqasm 3 add it as a comment
        return "// " + line + "\n"
    return line + "\n"


def convert_to_qasm3(qasm2_str: str):
    """Convert a QASM 2.0 string to QASM 3.0 string

    Args:
        qasm2_str (str): QASM 2.0 string
    """
    # pylint: disable=import-outside-toplevel
    from qiskit import QuantumCircuit

    try:
        # use inbuilt method to check validity
        _ = QuantumCircuit.from_qasm_str(qasm2_str)
    except Exception as e:
        raise ValueError("Invalid QASM 2.0 string") from e

    qasm3_str = "OPENQASM 3.0;\ninclude 'stdgates.inc';"

    # add the gate from qelib1.inc not present in the stdgates.inc file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(
        os.path.join(current_dir, "qelib_qasm3.qasm"), mode="r", encoding="utf-8"
    ) as gate_defs:
        for line in gate_defs:
            qasm3_str += line

    for line in qasm2_str.splitlines():
        line = _change_to_qasm_3(line)
        qasm3_str += line
    return qasm3_str

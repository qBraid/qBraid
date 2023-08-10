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
Module containing OpenQasm tools

"""
import os
import re
from collections import defaultdict
from typing import List

import numpy as np

from qbraid.interface.qbraid_qasm.qasm_preprocess import convert_to_supported_qasm
from qbraid.interface.qbraid_qasm.qelib1_defs import _decompose_rxx_instr

QASMType = str


def qasm_qubits(qasmstr: str) -> List[QASMType]:
    """Get number of qasm qubits.

    Args:
        qasmstr (str): OpenQASM 2 or OpenQASM 3 string

    Returns:
        List of qubits in the circuit
    """
    return [
        text.replace("\n", "")
        for match in re.findall(r"(\bqreg\s\S+\s+\b)|(qubit\[(\d+)\])", qasmstr)
        for text in match
        if text != "" and len(text) >= 2
    ]


def qasm_num_qubits(qasmstr: str) -> int:
    """Calculate number of qubits."""
    q_num = 0

    for num in qasm_qubits(qasmstr):
        q_num += int(re.search(r"\d+", num).group())
    return q_num


def qasm_depth(qasmstr: str) -> int:
    """Calculates circuit depth of OpenQASM 2 string"""
    qasm_input = convert_to_supported_qasm(qasmstr)
    lines = qasm_input.splitlines()

    gate_lines = [
        s
        for s in lines
        if s.strip() and not s.startswith(("OPENQASM", "include", "qreg", "gate", "//"))
    ]

    counts_dict = defaultdict(int)

    for s in gate_lines:
        matches = set(map(int, re.findall(r"q\[(\d+)\]", s)))

        # Calculate max depth among the qubits in the current line.
        max_depth = max(counts_dict[f"q[{i}]"] for i in matches)

        # Update depths for all qubits in the current line.
        for i in matches:
            counts_dict[f"q[{i}]"] = max_depth + 1

    return max(counts_dict.values()) if counts_dict else 0


def qasm3_depth(qasmstr: str) -> int:
    """Calculates circuit depth of OpenQASM 3 string"""
    # pylint: disable=import-outside-toplevel
    from qiskit.qasm3 import loads

    return loads(qasmstr).depth()


def _convert_to_contiguous_qasm(qasmstr: str, rev_qubits=False) -> QASMType:
    """Delete qubit with no gate and optional reverse circuit"""
    # pylint: disable=import-outside-toplevel
    from qbraid.interface.qbraid_cirq.tools import _convert_to_contiguous_cirq
    from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm, to_qasm

    circuit = to_qasm(_convert_to_contiguous_cirq(from_qasm(qasmstr), rev_qubits=rev_qubits))
    return circuit


def _unitary_from_qasm(qasmstr: QASMType) -> np.ndarray:
    """Return the unitary of the QASM"""
    # pylint: disable=import-outside-toplevel
    from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm

    return from_qasm(qasmstr).unitary()


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

    #  a newline separated qasm 2 string
    # formatted_qasm2 = circuit.qasm()
    qasm3_str = """OPENQASM 3.0;
include 'stdgates.inc';"""

    # add the gate from qelib1.inc not present in the
    # stdgates.inc file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(
        os.path.join(current_dir, "qasm_lib/qelib_qasm3.qasm"), mode="r", encoding="utf-8"
    ) as gate_defs:
        for line in gate_defs:
            qasm3_str += line

    for line in qasm2_str.splitlines():
        line = _change_to_qasm_3(line)
        qasm3_str += line
    return qasm3_str

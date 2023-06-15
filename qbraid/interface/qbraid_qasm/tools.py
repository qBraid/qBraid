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

import numpy as np
from cirq.circuits import Circuit
from qiskit.circuit import QuantumCircuit

from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm, to_qasm
from qbraid.transpiler.cirq_qasm.qelib1_defs import _decompose_rxx_instr

QASMType = str


def qasm_qubits(qasmstr: str) -> QASMType:
    """get number of qasm qubits"""

    return [
        text.replace("\n", "")
        for match in re.findall(r"(\bqreg\s\S+\s+\b)|(qubit\[(\d+)\])", qasmstr)
        for text in match
        if text != "" and len(text) >= 2
    ]


def qasm_num_qubits(qasmstr: str) -> QASMType:
    """calculate number of qubits"""
    q_num = 0

    for num in qasm_qubits(qasmstr):
        q_num += int(re.search(r"\d+", num).group())
    return q_num


def qasm_depth(qasmstr: str) -> QASMType:
    """calculate number of depth"""
    circuit = from_qasm(qasmstr)
    return len(Circuit(circuit.all_operations()))


def _convert_to_contiguous_qasm(qasmstr: str, rev_qubits=False) -> QASMType:
    """delete qubit with no gate and optional reverse circuit"""
    # pylint: disable=import-outside-toplevel
    from qbraid.interface.qbraid_cirq.tools import _convert_to_contiguous_cirq

    circuit = to_qasm(_convert_to_contiguous_cirq(from_qasm(qasmstr), rev_qubits=rev_qubits))
    return circuit


def _unitary_from_qasm(qasmstr: QASMType) -> np.ndarray:
    """Return the unitary of the QASM"""
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


def convert_to_qasm3(qasm_2_str: str):
    """Convert a QASM 2.0 string to QASM 3.0 string

    Args:
        qasm_2_str (str): QASM 2.0 string
    """
    try:
        # use inbuilt method to check validity
        _ = QuantumCircuit.from_qasm_str(qasm_2_str)
    except Exception as e:
        raise ValueError("Invalid QASM 2.0 string") from e

    #  a newline separated qasm 2 string
    # formatted_qasm_2 = circuit.qasm()
    qasm_3_str = """OPENQASM 3.0;
include 'stdgates.inc';"""

    # add the gate from qelib1.inc not present in the
    # stdgates.inc file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(
        os.path.join(current_dir, "qasm_lib/qelib_qasm3.qasm"), mode="r", encoding="utf-8"
    ) as gate_defs:
        for line in gate_defs:
            qasm_3_str += line

    for line in qasm_2_str.splitlines():
        line = _change_to_qasm_3(line)
        qasm_3_str += line
    return qasm_3_str

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
Module containing OpenQASM 2 tools

"""
import re
from collections import defaultdict
from typing import List

import numpy as np

from qbraid.interface.qbraid_qasm.qasm_preprocess import convert_to_supported_qasm

QASMType = str


def qasm_qubits(qasmstr: str) -> List[QASMType]:
    """Get number of qasm qubits.

    Args:
        qasmstr (str): OpenQASM 2 string

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
    """Calculate number of qubits in a qasm2 string."""
    q_num = 0

    for num in qasm_qubits(qasmstr):
        # split is needed as the name may contain
        # a number
        num = num.split("[")[1]
        q_num += int(re.search(r"\d+", num).group())
    return q_num


def qasm_depth(qasmstr: str) -> int:
    """Calculates circuit depth of OpenQASM 2 string"""
    qasm_input = convert_to_supported_qasm(qasmstr)
    lines = qasm_input.splitlines()

    gate_lines = [
        s
        for s in lines
        if s.strip() and not s.startswith(("OPENQASM", "include", "qreg", "creg", "gate", "//"))
    ]

    counts_dict = defaultdict(int)

    for s in gate_lines:
        matches = set(map(int, re.findall(r"q\[(\d+)\]", s)))

        if len(matches) == 0:
            continue

        # Calculate max depth among the qubits in the current line.
        max_depth = max(counts_dict[f"q[{i}]"] for i in matches)

        # Update depths for all qubits in the current line.
        for i in matches:
            counts_dict[f"q[{i}]"] = max_depth + 1

    return max(counts_dict.values()) if counts_dict else 0


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

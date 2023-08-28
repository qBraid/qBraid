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
from typing import List

import numpy as np

QASMType = str


def qasm_qubits(qasm_str: QASMType) -> List[str]:
    """Use regex to extract all qreg definitions from the string"""
    matches = re.findall(r"qreg (\w+)\[(\d+)\];", qasm_str)

    result = []
    for match in matches:
        var_name = match[0]
        n = int(match[1])
        result.extend([f"{var_name}[{i}]" for i in range(n)])

    return result


def qasm_num_qubits(qasmstr: QASMType) -> int:
    """Calculate number of qubits in a qasm2 string."""
    return len(qasm_qubits(qasmstr))


def _get_max_count(counts_dict):
    return max(counts_dict.values()) if counts_dict else 0


# pylint: disable=too-many-statements
def qasm_depth(qasm_str: QASMType) -> int:
    """Calculates circuit depth of OpenQASM 2 string"""
    lines = qasm_str.splitlines()

    # Keywords marking lines to ommit from depth calculation.
    not_counted = ("OPENQASM", "include", "qreg", "creg", "gate", "opaque", "//")
    gate_lines = [s for s in lines if s.strip() and not s.startswith(not_counted)]

    all_qubits = qasm_qubits(qasm_str)
    depth_counts = {qubit: 0 for qubit in all_qubits}

    track_measured = {}

    for _, s in enumerate(gate_lines):
        if s.startswith("barrier"):
            max_depth = _get_max_count(depth_counts)
            depth_counts = {key: max_depth for key in depth_counts.keys()}
            continue

        raw_matches = re.findall(r"(\w+)\[(\d+)\]", s)

        matches = []
        if len(raw_matches) == 0:
            try:
                if s.startswith("measure"):
                    match = re.search(r"measure (\w+) -> .+", s)
                    if match:
                        op = match.group(1)
                    else:
                        continue
                else:
                    op = s.split(" ")[-1].strip(";")
                for qubit in all_qubits:
                    qubit_name = qubit.split("[")[0]
                    if op == qubit_name:
                        matches.append(qubit)
            # pylint: disable=broad-exception-caught
            except Exception:
                continue

            if len(matches) == 0:
                continue
        else:
            for match in raw_matches:
                var_name = match[0]
                n = int(match[1])
                qubit = f"{var_name}[{n}]"
                if qubit in all_qubits and qubit in depth_counts:
                    matches.append(qubit)

        if s.startswith("if"):
            match = re.search(r"if\((\w+)==\d+\)", s)
            if match:
                creg = match.group(1)
                if creg in track_measured:
                    meas_qubits, meas_depth = track_measured[creg]
                    max_measured = max(max(depth_counts[q] for q in meas_qubits), meas_depth)
                    track_measured[creg] = meas_qubits, max_measured + 1
                    qubit = matches[0]
                    depth_counts[qubit] = max(max_measured, depth_counts[qubit]) + 1
                    continue

        # Calculate max depth among the qubits in the current line.
        max_depth = 0
        for qubit in matches:
            max_depth = max(max_depth, depth_counts[qubit])

        # Update depths for all qubits in the current line.
        for qubit in matches:
            depth_counts[qubit] = max_depth + 1

        if s.startswith("measure"):
            match = re.search(r"measure .+ -> (\w+)", s)
            if match:
                creg = match.group(1)
                track_measured[creg] = matches, max_depth + 1

    return _get_max_count(depth_counts)


def _convert_to_contiguous_qasm(qasm_str: QASMType, rev_qubits=False) -> QASMType:
    """Delete qubit with no gate and optional reverse circuit"""
    # pylint: disable=import-outside-toplevel
    from qbraid.interface.qbraid_cirq.tools import _convert_to_contiguous_cirq
    from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm, to_qasm

    return to_qasm(_convert_to_contiguous_cirq(from_qasm(qasm_str), rev_qubits=rev_qubits))


def _unitary_from_qasm(qasm_str: QASMType) -> np.ndarray:
    """Return the unitary of the QASM"""
    # pylint: disable=import-outside-toplevel
    from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm

    return from_qasm(qasm_str).unitary()

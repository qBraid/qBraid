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
import re

import numpy as np
from cirq.circuits import Circuit

from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm, to_qasm

QASMType = str


def qasm_qubits(qasmstr: str) -> QASMType:
    """get number of qasm qubits"""
    return [text.replace("\n", "") for text in re.findall(r"\bqreg\s\S+\s+\b", qasmstr)]


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

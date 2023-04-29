"""
Module containing pyQuil tools

"""
from typing import List, Optional, Union

import numpy as np
import re

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


from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm, to_qasm


def qasm_depth(qasmstr: str) -> QASMType:
    """calculate number of depth"""
    from cirq.circuits import Circuit

    circuit = from_qasm(qasmstr)
    return len(Circuit(circuit.all_operations()))


def _convert_to_contiguous_qasm(qasmstr: str, rev_qubits=False) -> QASMType:
    """delete qubit with no gate and optional reverse circuit"""
    from qbraid.interface.qbraid_cirq.tools import _convert_to_contiguous_cirq

    circuit = to_qasm(_convert_to_contiguous_cirq(from_qasm(qasmstr), rev_qubits=rev_qubits))
    return circuit


def _unitary_from_qasm(qasmstr: QASMType) -> np.ndarray:
    """Return the unitary of the QASM"""
    return from_qasm(qasmstr).unitary()

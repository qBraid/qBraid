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
Module containing Qiskit tools

"""
from collections import OrderedDict

import numpy as np
from openqasm3.parser import QASM3ParsingError, parse
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.qasm import QasmError
from qiskit.qasm3 import dumps, loads
from qiskit.quantum_info import Operator

QASMType = str


def _unitary_from_qiskit(circuit: QuantumCircuit) -> np.ndarray:
    """Return the unitary of a Qiskit quantum circuit."""
    return Operator(circuit).data


def _unitary_from_qasm3(qasmstr: QASMType) -> np.ndarray:
    """Return the unitary of the QASM 3 string"""
    circuit = loads(qasmstr)
    return _unitary_from_qiskit(circuit)


def _convert_to_contiguous_qiskit(circuit: QuantumCircuit) -> QuantumCircuit:
    """Delete qubit(s) with no gate, if any exist."""
    dag = circuit_to_dag(circuit)

    idle_wires = list(dag.idle_wires())
    for w in idle_wires:
        dag._remove_idle_wire(w)
        dag.qubits.remove(w)

    dag.qregs = OrderedDict()

    return dag_to_circuit(dag)


def _convert_to_contiguous_qasm3(qasmstr: QASMType) -> QASMType:
    """Delete qubit(s) with no gate, if any exist."""
    circuit = loads(qasmstr)
    circuit_contig = _convert_to_contiguous_qiskit(circuit)
    return dumps(circuit_contig)


def is_valid_qasm(qasm_str: str) -> bool:
    """Returns whether the input string represents a
    valid OpenQASM program.

    TODO: Verify that all exceptions that are caught"""
    parsers = {"OPENQASM 2.0": QuantumCircuit.from_qasm_str, "OPENQASM 3.0": parse}

    for version, parser in parsers.items():
        if version in qasm_str:
            try:
                parser(qasm_str)
                return True
            except (QasmError, QASM3ParsingError):
                return False

    return False

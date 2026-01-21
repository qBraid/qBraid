# Copyright (C) 2024 qBraid
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
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import weight

from qiskit.quantum_info import SparsePauliOp

if TYPE_CHECKING:
    import openfermion.ops.operators.qubit_operator as openfermion_


@weight(0.999)
def openfermion_qop_to_qiskit_qop(qubit_operator: openfermion_.QubitOperator) -> SparsePauliOp:
    """Returns SparsePauliOp given a openfermion QubitOperator.

    Args:
        circuit: Qiskit circuit to convert to OpenQASM 2 string.

    Returns:
        str: OpenQASM 2 representation of the input Qiskit circuit.
    """

    def pauli_of_to_string(pauli_op, n_qubits):
        """ Converts an Openfermion-style Pauli word to a string representation.
        The user must specify the total number of qubits.
        """
        p_string = ['I'] * n_qubits
        for i, p in pauli_op:
            p_string[i] = p
        return ''.join(p_string)
    from openfermion import count_qubits
    n_qubits = count_qubits(qubit_operator)

    # Convert each term sequencially.
    term_list = list()
    for term_tuple, coeff in qubit_operator.terms.items():
        term_string = pauli_of_to_string(term_tuple, n_qubits)

        # Reverse the string because of qiskit convention.
        term_list += [(term_string[::-1], coeff)]

    return SparsePauliOp.from_list(term_list)

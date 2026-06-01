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

from openfermion import QubitOperator

if TYPE_CHECKING:
    import qiskit.quantum_info as qiskit_


@weight(0.999)
def qiskit_qop_to_openfermion_qop(qubit_operator: qiskit_.SparsePauliOp) -> QubitOperator:
    """Returns openfermion QubitOperator equivalent to the qiskit SparsePauliOp

    Args:
        qubit_operator: qiskit SparsePauliOp to convert

    Returns:
        QubitOperator: QubitOperator equivalent of qubit_operator
    """

    # Create a dictionary to append all terms at once.
    terms_dict = dict()
    terms = qubit_operator.to_list()
    for term_string, coeff in terms:
        # Inversion of the string because of qiskit ordering.
        term_tuple = tuple([(i, p) for i, p in enumerate(term_string[::-1]) if p != 'I'])
        terms_dict[tuple(term_tuple)] = terms_dict.get(tuple(term_tuple), 0.) + coeff

    # Create and copy the information into a new QubitOperator.
    cirq_op = QubitOperator()
    cirq_op.terms = terms_dict

    return cirq_op

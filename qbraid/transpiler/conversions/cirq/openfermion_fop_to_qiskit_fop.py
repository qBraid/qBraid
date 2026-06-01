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

from qiskit_nature.second_q.operators import FermionicOp

if TYPE_CHECKING:
    import openfermion.ops.operators.fermion_operator as openfermion_


@weight(0.999)
def openfermion_fop_to_qiskit_fop(fermion_operator: openfermion_.FermionOperator) -> FermionicOp:
    """Returns SparsePauliOp given a openfermion QubitOperator.

    Args:
        fermion_operator: Openfermion FermionOperator to convert.

    Returns:
        FermionicOp: The qiskit fermion operator
    """

    updn = {0: "-_", 1: "+_"}

    # Convert each term sequencially.
    term_dict = dict()
    for term_tuple, coeff in fermion_operator.terms.items():
        fop = ""
        for m, ud in term_tuple:
            fop += updn[ud]+f"{m} "
        term_dict[fop[:-1] if fop else ""] = coeff
        # Reverse the string because of qiskit convention.

    return FermionicOp(term_dict)

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
Module for calculating unitary of quantum circuit/program

"""
from typing import TYPE_CHECKING, Optional

import numpy as np
from cirq.testing import assert_allclose_up_to_global_phase

from qbraid.exceptions import QbraidError

if TYPE_CHECKING:
    import qbraid


class UnitaryCalculationError(QbraidError):
    """Class for exceptions raised during unitary calculation"""


def circuits_allclose(  # pylint: disable=too-many-arguments
    circuit0: "qbraid.QPROGRAM",
    circuit1: "qbraid.QPROGRAM",
    index_contig: Optional[bool] = True,
    allow_rev_qubits: Optional[bool] = False,
    strict_gphase: Optional[bool] = False,
    atol: Optional[float] = 1e-7,
) -> bool:
    """Check if quantum program unitaries are equivalent.

    Args:
        circuit0 (:data:`~qbraid.QPROGRAM`): First quantum program to compare
        circuit1 (:data:`~qbraid.QPROGRAM`): Second quantum program to compare
        index_contig: If True, calculates circuit unitaries using contiguous qubit indexing.
        allow_rev_qubits: Whether to count identical circuits with reversed qubit ordering
            as equivalent.
        strict_gphase: If False, disregards global phase when verifying
            equivalence of the input circuit's unitaries.
        atol: Absolute tolerance parameter for np.allclose function.

    Returns:
        True if the input circuits pass unitary equality check

    """
    from qbraid import circuit_wrapper  # pylint: disable=import-outside-toplevel

    def unitary_equivalence_check(unitary0, unitary1, unitary_rev=None):
        if strict_gphase:
            return np.allclose(unitary0, unitary1) or (
                allow_rev_qubits and np.allclose(unitary0, unitary_rev)
            )
        try:
            assert_allclose_up_to_global_phase(unitary0, unitary1, atol=atol)
        except AssertionError:
            if allow_rev_qubits:
                try:
                    assert_allclose_up_to_global_phase(unitary0, unitary_rev, atol=atol)
                except AssertionError:
                    return False
            else:
                return False
        return True

    program0 = circuit_wrapper(circuit0)
    program1 = circuit_wrapper(circuit1)

    if index_contig:
        program0.convert_to_contiguous()
        program1.convert_to_contiguous()

    unitary0 = program0.unitary()
    unitary1 = program1.unitary()
    unitary_rev = program1.rev_qubits_unitary()

    return unitary_equivalence_check(unitary0, unitary1, unitary_rev)


def random_unitary_matrix(dim: int) -> np.ndarray:
    """Create a random (complex) unitary matrix of order `dim`

    Args:
        dim: integer square matrix dimension

    Returns:
        random unitary matrix of shape dim x dim
    """
    # Create a random complex matrix of size dim x dim
    matrix = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    # Use the QR decomposition to get a random unitary matrix
    unitary, _ = np.linalg.qr(matrix)
    return unitary

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
Module for calculating unitary of quantum circuit/program

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from qbraid.programs import load_program

if TYPE_CHECKING:
    import qbraid


def match_global_phase(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Matches the global phase of two numpy arrays.

    This function aligns the global phases of two matrices by applying a phase shift based
    on the position of the largest entry in one matrix. It computes and adjusts for the
    phase difference at this position, resulting in two phase-aligned matrices. The output,
    (a', b'), indicates that a' == b' is equivalent to a == b * exp(i * t) for some phase t.

    Args:
        a (np.ndarray): The first input matrix.
        b (np.ndarray): The second input matrix.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple of the two matrices `(a', b')`, adjusted for
                                       global phase. If shapes of `a` and `b` do not match or
                                       either is empty, returns copies of the original matrices.
    """
    if a.shape != b.shape or a.size == 0:
        return np.copy(a), np.copy(b)

    k = max(np.ndindex(*a.shape), key=lambda t: abs(b[t]))

    def dephase(v):
        r = np.real(v)
        i = np.imag(v)

        if i == 0:
            return -1 if r < 0 else 1
        if r == 0:
            return 1j if i < 0 else -1j

        return np.exp(-1j * np.arctan2(i, r))

    return a * dephase(a[k]), b * dephase(b[k])


def assert_allclose_up_to_global_phase(a: np.ndarray, b: np.ndarray, atol: float, **kwargs) -> None:
    """
    Checks if two numpy arrays are equal up to a global phase, within
    a specified tolerance, i.e. if a ~= b * exp(i t) for some t.

    Args:
        a (np.ndarray): The first input array.
        b (np.ndarray): The second input array.
        atol (float): The absolute error tolerance.
        **kwargs: Additional keyword arguments to pass to `np.testing.assert_allclose`.

    Raises:
        AssertionError: The matrices aren't nearly equal up to global phase.

    """
    a, b = match_global_phase(a, b)
    np.testing.assert_allclose(actual=a, desired=b, atol=atol, **kwargs)


def circuits_allclose(  # pylint: disable=too-many-arguments
    circuit0: qbraid.programs.QPROGRAM,
    circuit1: qbraid.programs.QPROGRAM,
    index_contig: bool = False,
    allow_rev_qubits: bool = False,
    strict_gphase: bool = False,
    atol: float = 1e-7,
) -> bool:
    """Check if quantum program unitaries are equivalent.

    Args:
        circuit0 (:data:`~qbraid.programs.QPROGRAM`): First quantum program to compare
        circuit1 (:data:`~qbraid.programs.QPROGRAM`): Second quantum program to compare
        index_contig: If True, calculates circuit unitaries using contiguous qubit indexing.
        allow_rev_qubits: Whether to count identical circuits with reversed qubit ordering
            as equivalent.
        strict_gphase: If False, disregards global phase when verifying
            equivalence of the input circuit's unitaries.
        atol: Absolute tolerance parameter for np.allclose function.

    Returns:
        True if the input circuits pass unitary equality check

    """

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

    program0 = load_program(circuit0)
    program1 = load_program(circuit1)

    if index_contig:
        program0.remove_idle_qubits()
        program1.remove_idle_qubits()

    unitary0 = program0.unitary()
    unitary1 = program1.unitary()
    unitary_rev = program1.unitary_rev_qubits()

    return unitary_equivalence_check(unitary0, unitary1, unitary_rev)

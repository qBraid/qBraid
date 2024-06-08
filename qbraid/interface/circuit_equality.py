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
from typing import TYPE_CHECKING

import jax
import jax.numpy as jnp

from qbraid.programs import load_program

if TYPE_CHECKING:
    import qbraid


@jax.jit
def match_global_phase(a: jnp.ndarray, b: jnp.ndarray) -> tuple[jnp.ndarray, jnp.ndarray]:
    """
    Matches the global phase of two JAX numpy arrays.

    This function aligns the global phases of two matrices by applying a phase shift based
    on the position of the largest entry in one matrix. It computes and adjusts for the
    phase difference at this position, resulting in two phase-aligned matrices. The output,
    (a', b'), indicates that a' == b' is equivalent to a == b * exp(i * t) for some phase t.

    Args:
        a (jnp.ndarray): The first input matrix.
        b (jnp.ndarray): The second input matrix.

    Returns:
        tuple[jnp.ndarray, jnp.ndarray]: A tuple of the two matrices `(a', b')`, adjusted for
                                         global phase. If shapes of `a` and `b` do not match or
                                         either is empty, returns copies of the original matrices.
    """
    if a.shape != b.shape or a.size == 0:
        return jnp.copy(a), jnp.copy(b)

    k = jnp.unravel_index(jnp.argmax(jnp.abs(b)), b.shape)
    phase_a = jnp.exp(-1j * jnp.angle(a[k]))
    phase_b = jnp.exp(-1j * jnp.angle(b[k]))

    return a * phase_a, b * phase_b


@jax.jit
def assert_allclose_up_to_global_phase(a: jnp.ndarray, b: jnp.ndarray, atol: float) -> None:
    """
    Checks if two JAX numpy arrays are equal up to a global phase, within
    a specified tolerance, i.e. if a ~= b * exp(i t) for some t.

    Args:
        a (jnp.ndarray): The first input array.
        b (jnp.ndarray): The second input array.
        atol (float): The absolute error tolerance.

    Raises:
        AssertionError: The matrices aren't nearly equal up to global phase.
    """
    a, b = match_global_phase(a, b)
    assert jnp.allclose(a, b, atol=atol), "The matrices aren't nearly equal up to global phase."


def circuits_allclose(
    circuit0: "qbraid.programs.QPROGRAM",
    circuit1: "qbraid.programs.QPROGRAM",
    index_contig: bool = False,
    allow_rev_qubits: bool = False,
    strict_gphase: bool = False,
    atol: float = 1e-7,
) -> bool:
    """
    Check if quantum program unitaries are equivalent using JAX.

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
        """
        Checks if two unitary matrices are equivalent up to global phase.

        Args:
            unitary0 (jnp.ndarray): First unitary matrix.
            unitary1 (jnp.ndarray): Second unitary matrix.
            unitary_rev (jnp.ndarray): Reversed qubit ordering unitary matrix (optional).

        Returns:
            bool: True if the unitaries are equivalent up to global phase.
        """
        if strict_gphase:
            return jnp.allclose(unitary0, unitary1, atol=atol) or (
                allow_rev_qubits and jnp.allclose(unitary0, unitary_rev, atol=atol)
            )
        try:
            assert_allclose_up_to_global_phase(unitary0, unitary1, atol)
        except AssertionError:
            if allow_rev_qubits:
                try:
                    assert_allclose_up_to_global_phase(unitary0, unitary_rev, atol)
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

    # Convert unitaries to JAX arrays for efficient computation
    unitary0 = jnp.array(program0.unitary())
    unitary1 = jnp.array(program1.unitary())
    unitary_rev = jnp.array(program1.unitary_rev_qubits()) if allow_rev_qubits else None

    return unitary_equivalence_check(unitary0, unitary1, unitary_rev)

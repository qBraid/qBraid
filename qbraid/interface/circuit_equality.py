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

import jax.numpy as jnp
from jax import device_put

from qbraid.programs import load_program

if TYPE_CHECKING:
    import qbraid


def match_global_phase(a: jnp.ndarray, b: jnp.ndarray) -> tuple[jnp.ndarray, jnp.ndarray]:
    """
    Matches the global phase of two JAX arrays.

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
        return jnp.array(a), jnp.array(b)

    # Move the data to the device (e.g., GPU) if not already there; JAX operations run on devices.
    a, b = device_put(a), device_put(b)

    k = max(jnp.ndindex(a.shape), key=lambda t: abs(b[t]))

    def dephase(v):
        r = jnp.real(v)
        i = jnp.imag(v)

        if i == 0:
            return -1 if r < 0 else 1
        if r == 0:
            return 1j if i < 0 else -1j

        return jnp.exp(-1j * jnp.arctan2(i, r))

    return a * dephase(a[k]), b * dephase(b[k])


def assert_allclose_up_to_global_phase(
    a: jnp.ndarray, b: jnp.ndarray, atol: float, **kwargs
) -> None:
    """
    Checks if two JAX arrays are equal up to a global phase, within
    a specified tolerance, i.e. if a ~= b * exp(i t) for some t.

    Args:
        a (jnp.ndarray): The first input array.
        b (jnp.ndarray): The second input array.
        atol (float): The absolute error tolerance.
        **kwargs: Additional keyword arguments to pass to the assertion check.

    Raises:
        AssertionError: The matrices aren't nearly equal up to global phase.

    """
    a, b = match_global_phase(a, b)

    # JAX arrays should be moved to device if not already; optional if you know they are on device
    a, b = device_put(a), device_put(b)

    # Perform the assertion manually since JAX does not have a direct assert_allclose equivalent
    if not jnp.allclose(a, b, atol=atol, **kwargs):
        max_diff = jnp.max(jnp.abs(a - b))
        message = (
            f"Arrays are not almost equal up to global phase (max difference {max_diff} > {atol})"
        )
        raise AssertionError(message)


def circuits_allclose(  # pylint: disable=too-many-arguments
    circuit0: "qbraid.programs.QPROGRAM",
    circuit1: "qbraid.programs.QPROGRAM",
    index_contig: bool = False,
    allow_rev_qubits: bool = False,
    strict_gphase: bool = False,
    atol: float = 1e-7,
) -> bool:
    """Check if quantum program unitaries are equivalent using JAX for computation.

    Args:
        circuit0 (:data:`~qbraid.programs.QPROGRAM`): First quantum program to compare
        circuit1 (:data:`~qbraid.programs.QPROGRAM`): Second quantum program to compare
        index_contig: If True, calculates circuit unitaries using contiguous qubit indexing.
        allow_rev_qubits: Whether to count identical circuits with reversed qubit ordering
            as equivalent.
        strict_gphase: If False, disregards global phase when verifying
            equivalence of the input circuit's unitaries.
        atol: Absolute tolerance parameter for jnp.allclose function.

    Returns:
        True if the input circuits pass unitary equality check
    """

    def unitary_equivalence_check(unitary0, unitary1, unitary_rev=None):
        if strict_gphase:
            return jnp.allclose(unitary0, unitary1, atol=atol) or (
                allow_rev_qubits and jnp.allclose(unitary0, unitary_rev, atol=atol)
            )
        try:
            assert_allclose_up_to_global_phase(unitary0, unitary1, atol=atol)
        except AssertionError:
            if allow_rev_qubits and unitary_rev is not None:
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
    unitary_rev = program1.unitary_rev_qubits() if allow_rev_qubits else None

    return unitary_equivalence_check(unitary0, unitary1, unitary_rev)

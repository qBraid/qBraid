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
Test circuit equality helper functions

"""
import numpy as np
import pytest

from qbraid.interface.circuit_equality import assert_allclose_up_to_global_phase, match_global_phase


def test_match_global_phase_basic1():
    """Test matching global phase of two arrays"""
    a = np.array([1 + 1j, 2 + 2j])
    b = np.array([1 - 1j, 2 - 2j])
    a_prime, b_prime = match_global_phase(a, b)
    np.testing.assert_allclose(a_prime, b_prime, atol=1e-10)


def test_match_global_phase_basic2():
    """Test matching global phase of two arrays"""
    a = np.array([[5, 4], [3, -2]])
    b = np.array([[0.000001, 0], [0, 1j]])
    c, d = match_global_phase(a, b)
    np.testing.assert_allclose(c, -a, atol=1e-10)
    np.testing.assert_allclose(d, b * -1j, atol=1e-10)


def test_match_global_phase_shape_mismatch1():
    """Test matching global phase of two arrays with shape mismatch"""
    a = np.array([1 + 1j, 2 + 2j])
    b = np.array([[1 - 1j, 2 - 2j]])
    a_prime, b_prime = match_global_phase(a, b)
    np.testing.assert_allclose(a, a_prime, atol=1e-10)
    np.testing.assert_allclose(b, b_prime, atol=1e-10)


def test_match_global_phase_shape_mismatch2():
    """Test matching global phase of two arrays with shape mismatch"""
    a = np.array([1])
    b = np.array([1, 2])
    c, d = match_global_phase(a, b)
    assert c.shape == a.shape
    assert d.shape == b.shape
    assert c is not a
    assert d is not b
    assert np.allclose(c, a)
    assert np.allclose(d, b)

    a = np.array([])
    b = np.array([])
    c, d = match_global_phase(a, b)
    assert c.shape == a.shape
    assert d.shape == b.shape
    assert c is not a
    assert d is not b
    assert np.allclose(c, a)
    assert np.allclose(d, b)


def test_match_global_phase_zeros():
    """Test matching global phase of two arrays where one is all zeros"""
    z = np.array([[0, 0], [0, 0]])
    b = np.array([[1, 1], [1, 1]])

    z1, b1 = match_global_phase(z, b)
    np.testing.assert_allclose(z, z1, atol=1e-10)
    np.testing.assert_allclose(b, b1, atol=1e-10)

    z2, b2 = match_global_phase(z, b)
    np.testing.assert_allclose(z, z2, atol=1e-10)
    np.testing.assert_allclose(b, b2, atol=1e-10)

    z3, z4 = match_global_phase(z, z)
    np.testing.assert_allclose(z, z3, atol=1e-10)
    np.testing.assert_allclose(z, z4, atol=1e-10)


def test_match_global_phase_invariance_to_phase_and_sign():
    """Test match global phase function remains invariant (or consistent) when the
    input arrays undergo transformations related to their phase or sign changes."""
    a = np.array([[1, 1.1], [-1.3, np.pi]])
    a2, _ = match_global_phase(a, a)
    a3, _ = match_global_phase(a * 1j, a * 1j)
    a4, _ = match_global_phase(-a, -a)
    a5, _ = match_global_phase(a * -1j, a * -1j)

    assert np.all(a2 == a)
    assert np.all(a3 == a)
    assert np.all(a4 == a)
    assert np.all(a5 == a)


def test_assert_allclose_up_to_global_phase_basic():
    """Test assert_allclose_up_to_global_phase with two arrays"""
    a = np.array([1 + 1j, 2 + 2j])
    b = np.array([1 - 1j, 2 - 2j])
    assert_allclose_up_to_global_phase(a, b, atol=1e-10)


def test_assert_allclose_up_to_global_phase_fail():
    """Test assert_allclose_up_to_global_phase with two arrays that are not close"""
    a = np.array([1 + 1j, 2 + 2j])
    b = np.array([10 + 10j, 20 + 20j])
    with pytest.raises(AssertionError):
        assert_allclose_up_to_global_phase(a, b, atol=1e-10)

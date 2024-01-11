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
Test circuit equality helper functions

"""

import numpy as np
import pytest

from qbraid.interface.circuit_equality import assert_allclose_up_to_global_phase, match_global_phase


def test_match_global_phase_basic():
    """Test matching global phase of two arrays"""
    a = np.array([1 + 1j, 2 + 2j])
    b = np.array([1 - 1j, 2 - 2j])
    a_prime, b_prime = match_global_phase(a, b)
    assert np.allclose(a_prime, b_prime)


def test_match_global_phase_shape_mismatch():
    """Test matching global phase of two arrays with shape mismatch"""
    a = np.array([1 + 1j, 2 + 2j])
    b = np.array([[1 - 1j, 2 - 2j]])
    a_prime, b_prime = match_global_phase(a, b)
    assert np.array_equal(a, a_prime) and np.array_equal(b, b_prime)


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

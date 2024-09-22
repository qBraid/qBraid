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
Unit tests for caching module.

"""
import math

import pytest

from qbraid._caching import _generate_cache_key, cached_method, clear_cache


class TestClass:
    """Test class for cached_method decorator."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    @cached_method
    def adjusted_factorial(self, n: int) -> int:
        """Calculate the factorial of n, adjusted by the instance attrs x and y."""
        base_factorial = math.factorial(n + self.x)
        return base_factorial**self.y

    def __hash__(self):
        return hash((self.x, self.y))


@pytest.fixture
def test_instance():
    return TestClass(1, 2)


def test_generate_cache_key(test_instance):
    """Test cache key generation."""
    key = _generate_cache_key(test_instance, "get_data", (1,), {})
    assert isinstance(key, str)
    assert len(key) == 64  # SHA-256 hash length


def test_clear_cache(test_instance, monkeypatch):
    """Test clearing the LRU cache."""
    monkeypatch.setenv("DISABLE_CACHE", "0")

    assert test_instance.adjusted_factorial.cache_info().currsize == 0

    for i in range(3):
        test_instance.adjusted_factorial(i)

    assert test_instance.adjusted_factorial.cache_info().currsize == 3

    clear_cache()

    assert test_instance.adjusted_factorial.cache_info().currsize == 0

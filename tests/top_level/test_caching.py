# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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


class ListArgClass:
    """Class with a cached method that accepts an unhashable (list) argument."""

    def __init__(self):
        self.call_count = 0

    @cached_method
    def total(self, items: list, offset: int = 0) -> int:
        """Sum ``items`` plus ``offset``; counts invocations of the real body."""
        self.call_count += 1
        return sum(items) + offset

    def __hash__(self):
        return id(self)


def test_cached_method_accepts_unhashable_args(monkeypatch):
    """A cached method can be called with list args and is cached.

    Regression: the previous implementation routed calls through ``functools.lru_cache``,
    which raised ``TypeError: unhashable type: 'list'``. The cache key is derived from a
    JSON serialization, so unhashable arguments are supported.
    """
    monkeypatch.setenv("DISABLE_CACHE", "0")
    obj = ListArgClass()
    obj.total.cache_clear()

    # Repeated identical call (incl. list arg) is served from cache: body runs once.
    assert obj.total([1, 2, 3], offset=10) == 16
    assert obj.total([1, 2, 3], offset=10) == 16
    assert obj.call_count == 1

    # A different list is a distinct key and re-invokes the body.
    assert obj.total([4, 5]) == 9
    assert obj.call_count == 2
    assert obj.total.cache_info().currsize == 2

    obj.total.cache_clear()
    assert obj.total.cache_info().currsize == 0


class BoundedClass:
    """Class whose cached method has a small ``maxsize`` to exercise eviction."""

    @cached_method(maxsize=2)
    def square(self, n: int) -> int:
        """Return ``n`` squared."""
        return n * n

    def __hash__(self):
        return id(self)


def test_cached_method_evicts_oldest_when_maxsize_reached(monkeypatch):
    """Once ``maxsize`` entries are cached, the oldest is evicted on the next miss."""
    monkeypatch.setenv("DISABLE_CACHE", "0")
    obj = BoundedClass()
    obj.square.cache_clear()

    obj.square(1)
    obj.square(2)
    assert obj.square.cache_info().currsize == 2

    # A third distinct key evicts the oldest entry; the cache stays bounded at maxsize.
    obj.square(3)
    assert obj.square.cache_info().currsize == 2

    obj.square.cache_clear()
    assert obj.square.cache_info().currsize == 0

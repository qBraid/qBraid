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
import time

import pytest

from qbraid._caching import _generate_cache_key, cache_disabled, cached_method, clear_cache


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

    def __init__(self):
        self.call_count = 0

    @cached_method(maxsize=2)
    def square(self, n: int) -> int:
        """Return ``n`` squared; counts invocations of the real body."""
        self.call_count += 1
        return n * n

    def __hash__(self):
        return id(self)


def test_cached_method_evicts_oldest_when_maxsize_reached(monkeypatch):
    """Once ``maxsize`` entries are cached, the oldest (by insertion) is evicted.

    Asserted via ``call_count`` rather than ``currsize`` alone: after a third distinct
    call evicts the oldest key, re-calling that key must recompute (body runs again)
    while the retained key is still served from cache.
    """
    monkeypatch.setenv("DISABLE_CACHE", "0")

    # Strictly-increasing timestamps so the "oldest" entry is unambiguous.
    ticks = iter(range(1, 1000))
    monkeypatch.setattr(time, "time", lambda: next(ticks))

    obj = BoundedClass()
    obj.square.cache_clear()

    assert obj.square(1) == 1  # cache: {1}
    assert obj.square(2) == 4  # cache: {1, 2}
    assert obj.square.cache_info().currsize == 2
    assert obj.call_count == 2

    # A third distinct key evicts the oldest entry (1); cache stays bounded at maxsize.
    assert obj.square(3) == 9  # evicts 1 -> cache: {2, 3}
    assert obj.square.cache_info().currsize == 2
    assert obj.call_count == 3

    # The retained key (2) is still cached: no recompute.
    assert obj.square(2) == 4
    assert obj.call_count == 3

    # The evicted key (1) must be recomputed: body runs again.
    assert obj.square(1) == 1
    assert obj.call_count == 4
    assert obj.square.cache_info().currsize == 2

    obj.square.cache_clear()
    assert obj.square.cache_info().currsize == 0


class CredentialedClass:
    """Class hashed by its 'credentials', mimicking QuantumProvider subclasses."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.call_count = 0

    def __hash__(self):
        return hash(self.api_key)

    @cached_method
    def get_data(self) -> str:
        """Return a value derived from the credentials; counts real invocations."""
        self.call_count += 1
        return f"data-for-{self.api_key}"


class UnhashableClass:
    """Class that defines ``__eq__`` without ``__hash__``, making instances unhashable."""

    def __init__(self):
        self.call_count = 0

    def __eq__(self, other):
        return isinstance(other, type(self))

    @cached_method
    def get_data(self) -> int:
        """Count real invocations."""
        self.call_count += 1
        return self.call_count


def test_cache_key_separates_instances_with_different_hashes(monkeypatch):
    """Instances with different hashes must not share cache entries.

    Regression: the cache key previously included only the class name, so two
    providers with different credentials shared entries — provider B could be
    served provider A's cached result. The key now includes ``hash(instance)``.
    """
    monkeypatch.setenv("DISABLE_CACHE", "0")
    CredentialedClass.get_data.cache_clear()

    alice = CredentialedClass("alice-key")
    bob = CredentialedClass("bob-key")

    assert alice.get_data() == "data-for-alice-key"
    # Different hash -> distinct key: bob must NOT receive alice's cached result.
    assert bob.get_data() == "data-for-bob-key"
    assert alice.call_count == 1
    assert bob.call_count == 1

    # Equal hash -> shared entry: a new instance with the same credentials hits the cache.
    alice2 = CredentialedClass("alice-key")
    assert alice2.get_data() == "data-for-alice-key"
    assert alice2.call_count == 0

    CredentialedClass.get_data.cache_clear()


def test_cache_key_falls_back_to_id_for_unhashable_instances(monkeypatch):
    """An unhashable instance (``__eq__`` without ``__hash__``) caches per-instance.

    ``hash(instance)`` raises ``TypeError`` for such classes; the key falls back to
    ``id(instance)`` instead of propagating the error, so each live instance gets
    its own entry.
    """
    monkeypatch.setenv("DISABLE_CACHE", "0")
    UnhashableClass.get_data.cache_clear()

    obj_a = UnhashableClass()
    obj_b = UnhashableClass()
    with pytest.raises(TypeError):
        hash(obj_a)

    # Each instance computes once, then is served from its own entry.
    assert obj_a.get_data() == 1
    assert obj_a.get_data() == 1
    assert obj_b.get_data() == 1
    assert obj_b.call_count == 1
    assert UnhashableClass.get_data.cache_info().currsize == 2

    UnhashableClass.get_data.cache_clear()


def test_cache_disabled_does_not_populate_cache(monkeypatch):
    """Calls made under ``cache_disabled`` recompute and leave the cache untouched.

    Previously the disabled path skipped only the cache *read*, still writing results
    and bumping stats. ``cache_disabled`` now bypasses the cache entirely.
    """
    monkeypatch.setenv("DISABLE_CACHE", "0")
    obj = BoundedClass()
    obj.square.cache_clear()

    with cache_disabled(obj):
        assert obj.square(2) == 4
        assert obj.square(2) == 4

    # Body ran every time and nothing was cached or counted as a hit/miss.
    assert obj.call_count == 2
    info = obj.square.cache_info()
    assert info.currsize == 0
    assert info.hits == 0
    assert info.misses == 0

    # Re-enabling caches normally again.
    assert obj.square(2) == 4
    assert obj.call_count == 3
    assert obj.square.cache_info().currsize == 1
    obj.square.cache_clear()

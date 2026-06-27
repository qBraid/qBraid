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
Functions and decorators for efficient caching to improve function and method performance.
Includes per-instance LRU caching, TTL expiration, and customizable caching for specific needs.

"""
import functools
import hashlib
import json
import os
import time
from collections import namedtuple
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional, TypeVar, overload

TFunc = TypeVar("TFunc", bound=Callable)


_CACHE_REGISTRY = []

# Mirrors the field layout of ``functools.lru_cache().cache_info()`` so callers
# relying on ``cache_info().currsize`` (etc.) keep working.
CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])


def _generate_cache_key(instance: Any, func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a cache key based on the class name, function name, args, and kwargs."""
    key_data = {
        "class_name": instance.__class__.__name__,
        "func_name": func_name,
        "args": args,
        "kwargs": kwargs,
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()


def _cached_method_wrapper(ttl: int = 120, maxsize: Optional[int] = 128) -> Callable:
    """A decorator to cache the results of methods with optional TTL and maxsize options.

    Entries are keyed by ``_generate_cache_key``, a SHA-256 of the JSON-serialized
    (class, method, args, kwargs). Because the key is derived from a JSON serialization
    rather than by hashing the raw arguments, decorated methods may be called with
    unhashable arguments (e.g. ``list`` / ``dict``) and still be cached — unlike a plain
    ``functools.lru_cache``, which raises ``TypeError: unhashable type`` for such args.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Maps cache key -> (result, timestamp). Keyed by the JSON-derived hash, so
        # unhashable positional/keyword arguments are supported.
        cache: dict[str, tuple[Any, float]] = {}
        stats = {"hits": 0, "misses": 0}

        def _evict_if_needed() -> None:
            # Bound the cache the way the previous lru_cache(maxsize) did, evicting the
            # oldest entry by insertion timestamp once the limit is reached.
            if maxsize is not None and len(cache) >= maxsize:
                oldest_key = min(cache, key=lambda k: cache[k][1])
                del cache[oldest_key]

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if os.getenv("DISABLE_CACHE") == "1":
                return func(self, *args, **kwargs)
            key = _generate_cache_key(self, func.__name__, args, kwargs)

            if not getattr(self, "__cache_disabled", False) and key in cache:
                cached_result, timestamp = cache[key]
                if (time.time() - timestamp) < ttl:
                    stats["hits"] += 1
                    return cached_result

            stats["misses"] += 1

            result = func(self, *args, **kwargs)
            _evict_if_needed()
            cache[key] = (result, time.time())
            return result

        def cache_clear() -> None:
            cache.clear()
            stats["hits"] = 0
            stats["misses"] = 0

        def cache_info() -> CacheInfo:
            return CacheInfo(
                hits=stats["hits"],
                misses=stats["misses"],
                maxsize=maxsize,
                currsize=len(cache),
            )

        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info
        wrapper.cache = cache

        _CACHE_REGISTRY.append(wrapper.cache_clear)

        return wrapper

    return decorator


# Function signatures with bounded TypeVar and overload pattern inspired by The Cirq Developers
# https://github.com/quantumlib/Cirq/blob/v1.4.1/cirq-core/cirq/_compat.py


@overload
def cached_method(__func: TFunc) -> TFunc: ...


@overload
def cached_method(*, maxsize: int = 128, ttl: int = 120) -> Callable[[TFunc], TFunc]: ...


def cached_method(
    func: Optional[TFunc] = None, *, maxsize: int = 128, ttl: int = 120
) -> Callable[[TFunc], TFunc]:
    """
    AD decorator that applies default caching behavior when used without arguments,
    or allows customization (e.g., maxsize, ttl) when used with arguments.

    Example usage:

    .. code-block:: python

        @cached_method
        def some_method(self, param):
            pass

        @cached_method(maxsize=200, ttl=300)
        def some_other_method(self, param):
            pass
    """

    def decorator(inner_func: TFunc) -> TFunc:
        return _cached_method_wrapper(ttl=ttl, maxsize=maxsize)(inner_func)

    return decorator if func is None else decorator(func)


@contextmanager
def cache_disabled(instance) -> Generator[None, None, None]:
    """
    Context manager to temporarily disable caching for a specific instance.

    Args:
        instance: The class instance for which the cache should be disabled.

    Example usage:

    .. code-block:: python

        with cache_disabled(instance):
            instance.method_call()
    """
    original_value = getattr(instance, "__cache_disabled", False)
    instance.__cache_disabled = True
    try:
        yield
    finally:
        instance.__cache_disabled = original_value


def clear_cache():
    """
    Clear all least-recently-used (LRU) caches that have been registered with the
    :py:func:`qbraid._caching.cached_method` decorator.

    Use this function to completely reset the cache state for all decorated methods, which
    can be useful in testing environments or when you need to free up memory by discarding
    cached results.
    """
    for cache_clear in _CACHE_REGISTRY:
        cache_clear()

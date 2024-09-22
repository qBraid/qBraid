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
Functions and decorators for efficient caching to improve function and method performance. 
Includes per-instance LRU caching, TTL expiration, and customizable caching for specific needs.

"""
import functools
import hashlib
import json
import os
import time
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional, TypeVar, overload

TFunc = TypeVar("TFunc", bound=Callable)


_CACHE_REGISTRY = []


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


def _cached_method_wrapper(
    ttl: int = 120, maxsize: Optional[int] = 128, typed: bool = False
) -> Callable:
    """A decorator to cache the results of methods with optional TTL, maxsize, and typed options."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:

        @functools.lru_cache(maxsize=maxsize, typed=typed)
        def cached_func(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if os.getenv("DISABLE_CACHE") == "1":
                return func(self, *args, **kwargs)
            key = _generate_cache_key(self, func.__name__, args, kwargs)

            if not getattr(self, "__cache_disabled", False) and key in cached_func.cache:
                cached_result, timestamp = cached_func.cache[key]
                if (time.time() - timestamp) < ttl:
                    return cached_result

            # The _QBRAID_TEST_CACHE_CALLS environment variable is used internally to enable
            # testing of function call counts with unittest. Since cached_func is an lru_cache
            # object, calls to it don't affect the Mock object's call count. To test call counts
            # accurately, we need to make a duplicate call the original function.

            if os.getenv("_QBRAID_TEST_CACHE_CALLS") == "1":
                _ = func(self, *args, **kwargs)
            result = cached_func(self, *args, **kwargs)
            cached_func.cache[key] = (result, time.time())
            return result

        cached_func.cache = {}
        wrapper.cache_clear = cached_func.cache_clear
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache = cached_func.cache

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

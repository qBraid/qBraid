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
Module for configuring provider credentials and authentication.

"""
import functools
import hashlib
import json
import time
from abc import ABC, abstractmethod


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate a cache key based on function name, args, and kwargs."""
    key_data = {"func_name": func_name, "args": args, "kwargs": kwargs}
    key_str = json.dumps(key_data, sort_keys=True)  # Ensure consistent key order
    return hashlib.sha256(key_str.encode()).hexdigest()


def cache_results(ttl: int = 120):
    """
    A decorator to cache the results of get_device or get_devices methods.

    Args:
        ttl (int): Time-to-live for the cache in seconds.
    """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # this is required to ensure new instances are not sharing the cache
            if not hasattr(self, "_device_cache"):
                self._device_cache = {}

            bypass_cache = kwargs.pop("bypass_cache", False)

            # Generate a unique cache key based on method name, args, and kwargs
            key = _generate_cache_key(func.__name__, args, kwargs)

            # Check if the result is in cache and still valid
            if not bypass_cache and key in self._device_cache:
                cached_result, timestamp = self._device_cache[key]
                if (time.time() - timestamp) < ttl:
                    return cached_result

            # Call the actual method and cache the result
            result = func(self, *args, **kwargs)
            self._device_cache[key] = (result, time.time())
            return result

        return wrapper

    return decorator


class QuantumProvider(ABC):
    """
    This class is responsible for managing the interactions and
    authentications with various Quantum services.

    """

    def save_config(self, **kwargs):
        """Saves account data and/or credentials to the disk."""
        raise NotImplementedError

    @abstractmethod
    @cache_results()
    def get_devices(self, bypass_cache: bool = False, **kwargs):
        """Return a list of backends matching the specified filtering.
        Use 'bypass_cache=True' kwarg to bypass the cache and fetch fresh data."""

    @abstractmethod
    @cache_results()
    def get_device(self, device_id: str, bypass_cache: bool = False):
        """Return quantum device corresponding to the specified device ID.
        Use 'bypass_cache=True' kwarg to bypass the cache and fetch fresh data."""

    def __eq__(self, other):
        """Equality comparison.

        By default, it is assumed that two `QuantumProviders` from the same class are
        equal. Subclassed providers can override this behavior.
        """
        return type(self).__name__ == type(other).__name__

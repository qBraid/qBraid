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

import time
from unittest.mock import Mock, patch

import pytest

from qbraid._caching import _generate_cache_key, cache_disabled, cached_method, clear_all_caches


class TestClass:

    @cached_method
    def get_data(self, param: int) -> int:
        return param * 2


@pytest.fixture
def test_instance():
    return TestClass()


def test_generate_cache_key(test_instance):
    """Test cache key generation."""
    key = _generate_cache_key(test_instance, "get_data", (1,), {})
    assert isinstance(key, str)
    assert len(key) == 64  # SHA-256 hash length

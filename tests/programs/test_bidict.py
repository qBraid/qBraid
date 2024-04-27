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
Unit tests for bidirectional dictionary.

"""

import pytest

from qbraid.programs.bidict import BiDict


def test_add_and_get():
    """Test adding and getting key-value pairs."""
    b = BiDict()
    b.add("apple", 1)
    assert b.get_value("apple") == 1
    assert b.get_key(1) == "apple"
    with pytest.raises(ValueError):
        b.add("apple", 2)
    with pytest.raises(ValueError):
        b.add("pear", 1)


def test_overwrite():
    """Test overwriting key-value pairs."""
    b = BiDict()
    b.add("apple", 1)
    b.add("apple", 2, overwrite=True)
    assert b.get_value("apple") == 2
    assert b.get_key(2) == "apple"


def test_remove():
    """Test removing key-value pairs."""
    b = BiDict()
    b.add("apple", 1)
    b.remove_by_key("apple")
    assert "apple" not in b
    assert b.get_value("apple") is None
    b.add("banana", 2)
    b.remove_by_value(2)
    assert "banana" not in b
    assert b.get_key(2) is None


def test_len():
    """Test getting the length of the bidirectional dictionary."""
    b = BiDict()
    assert len(b) == 0
    b.add("apple", 1)
    assert len(b) == 1
    b.add("banana", 2)
    assert len(b) == 2
    b.remove_by_key("apple")
    assert len(b) == 1

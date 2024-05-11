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
Unit tests for defining and updating runtime conversion schemes

"""

import pytest

from qbraid.transpiler.scheme import ConversionScheme


def test_initialization():
    """Test the initialization and default values of the ConversionScheme."""
    cs = ConversionScheme()
    assert cs.conversion_graph is None
    assert cs.max_path_attempts == 3
    assert cs.max_path_depth is None
    assert len(cs.extra_kwargs) == 0


def test_update_values():
    """Test the dynamic update of the ConversionScheme's attributes."""
    cs = ConversionScheme()
    cs.update_values(max_path_attempts=5, max_path_depth=2, extra_kwargs={"new_key": "new_value"})
    assert cs.max_path_attempts == 5
    assert cs.max_path_depth == 2
    assert cs.extra_kwargs == {"new_key": "new_value"}

    # Test updating nested kwargs
    cs.update_values(extra_kwargs={"new_key": "updated_value"})
    assert cs.extra_kwargs["new_key"] == "updated_value"


def test_update_invalid_attribute():
    """Test updating an invalid attribute which should raise an AttributeError."""
    cs = ConversionScheme()
    with pytest.raises(AttributeError):
        cs.update_values(invalid_key="value")


def test_str_method():
    """Test the string representation of the ConversionScheme."""
    cs = ConversionScheme(
        conversion_graph=None,
        max_path_attempts=2,
        max_path_depth=1,
        extra_kwargs={"require_native": True},
    )
    expected_str = (
        "ConversionScheme(conversion_graph=None, max_path_attempts=2, "
        "max_path_depth=1, require_native=True)"
    )
    assert str(cs) == expected_str

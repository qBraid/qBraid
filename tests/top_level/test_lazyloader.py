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
Unit tests for the LazyLoader class.

"""
import sys

import pytest

from qbraid._import import LazyLoader


def test_lazy_loading():
    """Test that the module is not loaded until an attribute is accessed."""
    # Remove the module from sys.modules if it's already loaded
    if "calendar" in sys.modules:
        del sys.modules["calendar"]

    calendar_loader = LazyLoader("calendar", globals())
    assert "calendar" not in sys.modules, "Module 'calendar' should not be loaded yet"

    # Access an attribute to trigger loading
    _ = calendar_loader.month_name
    assert (
        "calendar" in sys.modules
    ), "Module 'calendar' should be loaded after accessing an attribute"


def test_parent_globals_update():
    """Test that the parent's globals are updated after loading."""
    if "math" in sys.modules:
        del sys.modules["math"]

    math_loader = LazyLoader("math", globals())
    assert "math" not in globals(), "Global namespace should not initially contain 'math'"

    _ = math_loader.pi
    assert "math" in globals(), "Global namespace should contain 'math' after loading"


def test_attribute_access():
    """Test that attributes of the loaded module can be accessed."""
    math_loader = LazyLoader("math", globals())
    assert math_loader.pi == pytest.approx(
        3.141592653589793
    ), "Attribute 'pi' should match the math module's 'pi'"


def test_invalid_attribute():
    """Test accessing an invalid attribute."""
    math_loader = LazyLoader("math", globals())
    with pytest.raises(AttributeError):
        _ = math_loader.invalid_attribute

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
Unit tests for lazy imports and loading entry points.

"""
from unittest.mock import Mock as MockEntryPoint
from unittest.mock import patch

import pytest

from qbraid._import import _load_entrypoint
from qbraid.exceptions import QbraidError


def test_load_entrypoint_success():
    """Test that an entrypoint is successfully loaded."""
    module = "programs"
    name = "qasm3"
    assert _load_entrypoint(module, name).__name__ == "OpenQasm3Program"


def test_load_entrypoint_raise_value_error():
    """Test that a ValueError is raised when the entrypoint is not found."""
    module = "programs"
    name = "nonexistent"

    with pytest.raises(ValueError) as excinfo:
        _load_entrypoint(module, name)
    assert f"Entrypoint '{name}' not found in module '{module}'." in str(excinfo.value)


def test_load_entrypoint_raise_qbraid_error():
    """Test that a QbraidError is raised when loading an entrypoint fails."""
    module = "programs"
    name = "qasm3"

    with patch(
        "importlib.metadata.entry_points", return_value={"qbraid.programs": [MockEntryPoint()]}
    ):
        with pytest.raises(QbraidError) as excinfo:
            _load_entrypoint(module, name)
        assert f"Failed to load entrypoint '{name}' from module '{module}'." in str(excinfo.value)

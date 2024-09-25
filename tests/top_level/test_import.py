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
Unit tests for lazy loading of modules, objects and entry points

"""
import sys
from unittest.mock import MagicMock
from unittest.mock import Mock as MockEntryPoint
from unittest.mock import patch

import pytest

import qbraid
from qbraid._entrypoints import get_entrypoints, load_entrypoint
from qbraid.exceptions import QbraidError
from qbraid.programs._import import _dynamic_importer


def test_load_entrypoint_success():
    """Test that an entrypoint is successfully loaded."""
    module = "programs"
    name = "qasm3"
    assert load_entrypoint(module, name).__name__ == "OpenQasm3Program"


def test_load_entrypoint_raise_value_error():
    """Test that a ValueError is raised when the entrypoint is not found."""
    module = "programs"
    name = "nonexistent"

    with pytest.raises(ValueError) as excinfo:
        load_entrypoint(module, name)
    assert f"Entrypoint '{name}' not found in module '{module}'." in str(excinfo.value)


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10 or higher")
def test_load_entrypoint_raise_qbraid_error():
    """Test that a QbraidError is raised when loading an entrypoint fails."""
    module = "programs"
    name = "qasm3"

    with patch(
        "importlib.metadata.entry_points", return_value={"qbraid.programs": [MockEntryPoint()]}
    ):
        with pytest.raises(QbraidError) as excinfo:
            load_entrypoint(module, name)
        assert f"Failed to load entrypoint '{name}' from module '{module}'." in str(excinfo.value)


def mock_get_class(name):
    return type(name, (), {})


def mock_assign_default_type_alias(imported, program_type):
    return "mock_alias"


def test_dynamic_importer_exception():
    opt_modules = ["nonexistent.module"]

    with patch("qbraid.programs._import.import_module", side_effect=Exception("Import error")):
        with patch("qbraid.programs._import._get_class", side_effect=mock_get_class):
            with patch(
                "qbraid.programs._import._assign_default_type_alias",
                side_effect=mock_assign_default_type_alias,
            ):
                imported = _dynamic_importer(opt_modules)
                assert imported == {}


@patch("qbraid._entrypoints.importlib.metadata.entry_points")
@patch("qbraid._entrypoints.pkg_resources.iter_entry_points")
@patch("qbraid._entrypoints.sys.version_info")
def test_get_entrypoints_with_old_python_version(
    mock_version_info, mock_pkg_resources_eps, mock_importlib_eps
):
    """Test that entry points are retrieved correctly with an old Python version."""
    mock_version_info.__ge__.return_value = False

    mock_entry_point = MagicMock()
    mock_entry_point.name = "qasm2"
    mock_pkg_resources_eps.return_value = [mock_entry_point]

    result = get_entrypoints("programs")

    assert result == {"qasm2": mock_entry_point}

    mock_pkg_resources_eps.assert_called_once_with(group="qbraid.programs")
    mock_importlib_eps.assert_not_called()


@patch("qbraid._entrypoints.importlib.metadata.entry_points")
@patch("qbraid._entrypoints.pkg_resources.iter_entry_points")
@patch("qbraid._entrypoints.sys.version_info")
def test_get_entrypoints_with_new_python_version(
    mock_version_info, mock_pkg_resources_eps, mock_importlib_eps
):
    """Test that entry points are retrieved correctly with Python 3.10+."""
    mock_version_info.__ge__.return_value = True

    mock_entry_point = MagicMock()
    mock_entry_point.name = "qasm2"
    mock_importlib_eps.return_value.select.return_value = [mock_entry_point]

    result = get_entrypoints("programs")

    assert result == {"qasm2": mock_entry_point}

    mock_importlib_eps.return_value.select.assert_called_once_with(group="qbraid.programs")
    mock_pkg_resources_eps.assert_not_called()


@pytest.mark.parametrize("module_name", list(qbraid._lazy.keys()))
def test_lazy_loading_modules(module_name):
    """Test lazy loading of modules."""
    mod = getattr(qbraid, module_name)
    assert mod is not None
    assert mod.__name__.endswith(f".{module_name}")


@pytest.mark.parametrize(
    "obj_name", [item for sublist in qbraid._lazy.values() for item in sublist]
)
def test_lazy_loading_objects(obj_name):
    """Test lazy loading of objects."""
    obj = getattr(qbraid, obj_name)
    assert obj is not None
    assert hasattr(qbraid, obj_name)

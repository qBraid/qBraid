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
Unit tests for the about module.

"""

import sys
from importlib.metadata import PackageNotFoundError, distribution, version
from io import StringIO
from unittest.mock import patch

import numpy
import openqasm3
import pydantic
import pyqasm
import qbraid_core
import rustworkx

from qbraid import _about
from qbraid._version import __version__

PYQASM_VERSION = version("pyqasm")
PYQASM_VERSION_BUG = PYQASM_VERSION in {"0.2.0", "0.2.1"}

TYPING_EXTS_VERSION = version("typing-extensions")


def test_about():
    """Test the about function."""

    # Redirect stdout to capture the output of the about function
    captured_output = StringIO()
    sys.stdout = captured_output

    _about.about()

    # Restore stdout
    sys.stdout = sys.__stdout__

    # Get the captured output as a string
    output = captured_output.getvalue()

    core_dependencies = {
        "numpy": numpy.__version__,
        "openqasm3": openqasm3.__version__,
        "pyqasm": pyqasm.__version__ if not PYQASM_VERSION_BUG else PYQASM_VERSION,
        "pydantic": pydantic.__version__,
        "qbraid-core": qbraid_core.__version__,
        "rustworkx": rustworkx.__version__,
        "typing-extensions": TYPING_EXTS_VERSION,
    }

    assert f"qbraid:\t{__version__}\n\n" in output
    assert "Core Dependencies" in output
    for dep, v in core_dependencies.items():
        assert f"{dep}: {v}" in output
    assert "Optional Dependencies" in output
    assert "Python:" in output
    assert "Platform:" in output


def test_about_no_optional_dependencies():
    """Test the about function when no optional dependencies are available."""
    _, extras = _about.get_dependencies("qbraid")
    optional_packages = {item for subset in extras.values() for item in subset}

    def custom_distribution(name):
        if any(dep in name for dep in optional_packages):
            raise PackageNotFoundError
        return distribution(name)

    with patch("importlib.metadata.distribution", side_effect=custom_distribution):
        with patch("builtins.print") as mock_print:
            _about.about()
            actual_print_args = " ".join([str(arg[0]) for arg in mock_print.call_args_list])
            assert "None" in actual_print_args

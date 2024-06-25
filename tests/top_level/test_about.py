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
from io import StringIO
from unittest.mock import Mock, patch

from qbraid import _about


def test_about():
    """Test the about function."""
    # Redirect stdout to capture the output of the about function
    captured_output = StringIO()
    sys.stdout = captured_output

    # Call the about function
    _about.about()

    # Restore stdout
    sys.stdout = sys.__stdout__

    # Get the captured output as a string
    output = captured_output.getvalue()

    assert "qbraid:" in output

    # Verify core dependencies are mentioned in the output
    assert "Core Dependencies" in output
    assert "rustworkx:" in output
    assert "numpy:" in output
    assert "openqasm3:" in output
    assert "qbraid_core:" in output

    # Verify the presence of optional dependencies section
    assert "Optional Dependencies" in output

    # Verify Python and platform information is present
    assert "Python:" in output
    assert "Platform:" in output


def test_about_no_optional_dependencies():
    """Test the about function when no optional dependencies are available."""
    optional_dependencies = [
        "qbraid_qir",
        "braket._sdk",
        "cirq",
        "pyquil",
        "pennylane",
        "pytket",
        "qiskit",
        "qiskit_ibm_runtime",
    ]

    original_import = __builtins__["__import__"]

    def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
        if any(dep in name for dep in optional_dependencies):
            raise ImportError(f"No module named '{name}'")
        else:
            return original_import(name, globals, locals, fromlist, level)

    with patch("builtins.__import__", side_effect=custom_import):
        with patch("builtins.print") as mock_print:
            _about.about()
            actual_print_args = " ".join([str(arg[0]) for arg in mock_print.call_args_list])
            assert "None" in actual_print_args

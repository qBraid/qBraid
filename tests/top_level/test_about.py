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
from importlib.metadata import PackageNotFoundError, distribution
from io import StringIO
from unittest.mock import patch

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
    assert "qbraid-core:" in output
    assert "pydantic:" in output

    # Verify the presence of optional dependencies section
    assert "Optional Dependencies" in output

    # Verify Python and platform information is present
    assert "Python:" in output
    assert "Platform:" in output


def test_about_no_optional_dependencies():
    """Test the about function when no optional dependencies are available."""
    optional_packages = [
        "qbraid-qir",
        "amazon-braket-sdk",
        "cirq-core",
        "pyquil",
        "pennylane",
        "pytket",
        "qiskit",
        "qiskit-ibm-runtime",
        "oqc-qcaas-client",
    ]

    def custom_distribution(name):
        if any(dep in name for dep in optional_packages):
            raise PackageNotFoundError
        return distribution(name)

    with patch("importlib.metadata.distribution", side_effect=custom_distribution):
        with patch("builtins.print") as mock_print:
            _about.about()
            actual_print_args = " ".join([str(arg[0]) for arg in mock_print.call_args_list])
            assert "None" in actual_print_args

# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
"""
Unit test for the graph-based transpiler

"""

from unittest.mock import Mock

import braket.circuits
import pytest

from qbraid.exceptions import PackageValueError, ProgramTypeError
from qbraid.interface.converter import (
    _convert_path_to_string,
    _get_program_type,
    convert_to_package,
)

from ..fixtures.programs import bell_data

bell_map, _ = bell_data()

# Define the test data
packages = ["braket", "cirq", "pyquil", "qiskit", "pytket", "qasm2", "qasm3"]
test_data = [(bell_map[package](), package) for package in packages]


@pytest.mark.parametrize("program,expected_package", test_data)
def test_get_program_type(program, expected_package):
    """Test that the correct package is returned for a given program."""
    assert _get_program_type(program) == expected_package


def test_raise_error_unuspported_source_program():
    """Test that an error is raised if source program is not supported."""
    with pytest.raises(PackageValueError):
        _get_program_type(Mock())


@pytest.mark.parametrize(
    "item",
    ["OPENQASM 2.0; bad operation", "OPENQASM 3.0; bad operation", "DECLARE ro BIT[1]", "circuit"],
)
def test_bad_source_openqasm_program(item):
    """Test raising ProgramTypeError converting invalid OpenQASM program string"""
    with pytest.raises(ProgramTypeError):
        _get_program_type(item)


@pytest.mark.parametrize("item", [1, None])
def test_bad_source_program_type(item):
    """Test raising ProgramTypeError converting circuit of non-supported type"""
    with pytest.raises(ProgramTypeError):
        _get_program_type(item)


def test_unuspported_target_package():
    """Test that an error is raised if target package is not supported."""
    with pytest.raises(PackageValueError):
        convert_to_package(braket.circuits.Circuit(), "alice")


def test_convert_path_to_string():
    """Test formatted conversion path logging helper function."""
    # Example conversion path
    path = ["cirq_to_qasm2", "qasm2_to_qiskit", "qiskit_to_qasm3"]
    expected_output = "cirq -> qasm2 -> qiskit -> qasm3"

    # Call the function and assert the result
    assert (
        _convert_path_to_string(path) == expected_output
    ), "The function did not return the expected string"

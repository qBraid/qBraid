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
import braket.circuits
import pytest

from qbraid.exceptions import PackageValueError
from qbraid.interface.converter import convert_to_package


def test_unuspported_target_package():
    """Test that an error is raised if target package is not supported."""
    with pytest.raises(PackageValueError):
        convert_to_package(braket.circuits.Circuit(), "alice")


# def test_convert_path_to_string():
#     """Test formatted conversion path logging helper function."""
#     # Example conversion path
#     path = ["cirq_to_qasm2", "qasm2_to_qiskit", "qiskit_to_qasm3"]
#     expected_output = "cirq -> qasm2 -> qiskit -> qasm3"

#     # Call the function and assert the result
#     assert (
#         _convert_path_to_string(path) == expected_output
#     ), "The function did not return the expected string"

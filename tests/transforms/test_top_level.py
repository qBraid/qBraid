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
Unit tests for top-level functions and exceptions in the transforms module

"""

import pytest

from qbraid.transforms.exceptions import DeviceProgramTypeMismatchError


class MockProgram:
    """Mock class for testing DeviceProgramTypeMismatchError."""


def get_expected_message(program, expected_type, action_type):
    """Generate the expected error message dynamically."""
    if program is None:
        program_type = "NoneType"
    else:
        program_type = type(program).__name__
    return (
        f"Incompatible program type: '{program_type}'. "
        f"Device action type '{action_type}' requires a program of type '{expected_type}'."
    )


@pytest.mark.parametrize(
    "program, expected_type, action_type",
    [
        (MockProgram(), "QuantumProgram", "Compute"),
        (object(), "QuantumProgram", "Compute"),
        (MockProgram(), "MockProgram", "Compute"),
        (None, "QuantumProgram", "Compute"),
    ],
)
def test_device_program_type_mismatch_error(program, expected_type, action_type):
    """Test DeviceProgramTypeMismatchError with various scenarios."""
    expected_message = get_expected_message(program, expected_type, action_type)
    with pytest.raises(DeviceProgramTypeMismatchError) as exc_info:
        raise DeviceProgramTypeMismatchError(program, expected_type, action_type)

    assert str(exc_info.value) == expected_message

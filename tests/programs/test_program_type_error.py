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
Unit tests for ProgramTypeError
"""

from qbraid.programs.exceptions import ProgramTypeError


def test_program_type_error():
    """Test the ProgramTypeError class."""
    error = ProgramTypeError(program="test")
    message = error.generate_message()
    assert message == "Quantum program of type '<class 'str'>' is not supported."

    error = ProgramTypeError()
    message = error.generate_message()
    assert message == "Unsupported quantum program type."

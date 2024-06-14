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
Module defining exceptions for errors raised by qBraid transforms.

"""

from qbraid.exceptions import QbraidError


class TransformError(QbraidError):
    """Base class for errors raised during qBraid transform processes."""


class DecompositionError(TransformError):
    """For errors raised during circuit decomposition processes."""


class DeviceProgramTypeMismatchError(TypeError, TransformError):
    """
    Exception raised when the program type does not match the device action type.

    """

    def __init__(self, program, expected_type, action_type):
        message = (
            f"Incompatible program type: '{type(program).__name__}'. "
            f"Device action type '{action_type}' "
            f"requires a program of type '{expected_type}'."
        )
        super().__init__(message)

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
Module defining exceptions for errors raised while processing a device.

"""
from qbraid.exceptions import QbraidError


class ProgramValidationError(QbraidError):
    """Base class for errors raised while validating a quantum program."""


class QbraidRuntimeError(QbraidError):
    """Base class for errors raised while submitting a quantum job."""


class ResourceNotFoundError(QbraidError):
    """Exception raised when the desired resource could not be found."""


class JobStateError(QbraidError):
    """Class for errors raised due to the state of a quantum job"""


class DeviceProgramTypeMismatchError(ProgramValidationError):
    """
    Exception raised when the program type does not match the Experiment type.

    """

    def __init__(self, program, expected_type, experiment_type):
        message = (
            f"Incompatible program type: '{type(program).__name__}'. "
            f"Experiment type '{experiment_type}' "
            f"requires a program of type '{expected_type}'."
        )
        super().__init__(message)

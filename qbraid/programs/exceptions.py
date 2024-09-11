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
Module defining exceptions for errors raised by qBraid.

"""
from typing import Any, Optional

from qbraid_core._import import LazyLoader

from qbraid.exceptions import QbraidError

registry = LazyLoader("registry", globals(), "qbraid.programs.registry")


class QasmError(QbraidError):
    """For errors raised while processing OpenQASM programs."""


class TransformError(QbraidError):
    """Base class for errors raised during qBraid transform processes."""


class PackageValueError(QbraidError):
    """Class for errors raised due to unsupported quantum frontend package"""

    def __init__(self, package: str):
        msg = (
            f"Quantum frontend module '{package}' is not supported.\n"
            f"Frontends supported by qBraid are: {registry.QPROGRAM_ALIASES}"
        )
        super().__init__(msg)


class ProgramTypeError(QbraidError):
    """Exception raised for errors encountered with unsupported quantum programs.

    Attributes:
        program (Optional[Any]): The program that caused the error, default is None.
        message (Optional[str]): Explanation of the error. If None, a default error message
                                 is generated based on the provided program.
    """

    def __init__(self, program: Optional[Any] = None, message: Optional[str] = None):
        self.program = program
        self.message = message
        super().__init__(self.generate_message())

    def generate_message(self) -> str:
        """Generate an error message based on the input."""
        if self.message is not None:
            return self.message
        if self.program is not None:
            return f"Quantum program of type '{type(self.program)}' is not supported."
        return "Unsupported quantum program type."


class ValidationError(ProgramTypeError):
    """Custom exception for validation errors in program types."""

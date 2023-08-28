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
Module defining exceptions for errors raised by qBraid.

"""

from ._qprogram import QPROGRAM_LIBS


class QbraidError(Exception):
    """Base class for errors raised by qBraid."""


class PackageValueError(QbraidError):
    """Class for errors raised due to unsupported quantum frontend package"""

    def __init__(self, package):
        msg = (
            f"Quantum frontend module {package} is not supported.\n"
            f"Frontends supported by qBraid are: {QPROGRAM_LIBS}"
        )
        super().__init__(msg)


class ProgramTypeError(QbraidError):
    """Class for errors raised when processing unsupported quantum programs"""

    def __init__(self, program):
        msg = f"Quantum program of type {type(program)} is not supported."
        super().__init__(msg)


class VisualizationError(QbraidError):
    """Class for errors raised when using visualization features."""


class QasmError(QbraidError):
    """For errors raised while processing OpenQASM programs."""

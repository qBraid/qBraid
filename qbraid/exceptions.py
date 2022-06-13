"""
Module defining exceptions for errors raised by qBraid.

"""
from ._typing import SUPPORTED_PROGRAM_TYPES

# Supported quantum frontend packages.
_SUPPORTED_PKGS = list(SUPPORTED_PROGRAM_TYPES.keys())


class QbraidError(Exception):
    """Base class for errors raised by qBraid."""


class PackageValueError(QbraidError):
    """Class for errors raised due to unsupported quantum frontend package"""

    def __init__(self, package):
        msg = (
            f"Quantum frontend module {package} is not supported.\n"
            f"Frontends supported by qBraid are: {_SUPPORTED_PKGS}"
        )
        super().__init__(msg)


class ProgramTypeError(QbraidError):
    """Class for errors raised when processing unsupported quantum programs"""

    def __init__(self, program):
        msg = (
            f"Quantum program of type {type(program)} is not supported.\n"
            f"Program types supported by qBraid are:\n{SUPPORTED_PROGRAM_TYPES}"
        )
        super().__init__(msg)

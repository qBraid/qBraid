"""
Module defining exceptions for errors raised by qBraid.

"""

from ._qprogram import SUPPORTED_FRONTENDS


class QbraidError(Exception):
    """Base class for errors raised by qBraid."""


class PackageValueError(QbraidError):
    """Class for errors raised due to unsupported quantum frontend package"""

    def __init__(self, package):
        msg = (
            f"Quantum frontend module {package} is not supported.\n"
            f"Frontends supported by qBraid are: {SUPPORTED_FRONTENDS}"
        )
        super().__init__(msg)


class ProgramTypeError(QbraidError):
    """Class for errors raised when processing unsupported quantum programs"""

    def __init__(self, program):
        msg = f"Quantum program of type {type(program)} is not supported."
        super().__init__(msg)

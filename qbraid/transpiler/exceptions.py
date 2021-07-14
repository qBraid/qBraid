"""Exceptions for errors raised while handling circuits."""

from qbraid.exceptions import QbraidError


class TranspileError(QbraidError):
    """Base class for errors raised while transpiling a circuit."""

    pass

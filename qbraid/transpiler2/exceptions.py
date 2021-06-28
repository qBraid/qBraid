"""Exceptions for errors raised while handling circuits."""

from qbraid.exceptions import QbraidError


class ParsingError(QbraidError):
    """Base class for errors raised while processing a circuit."""

    pass

"""Exceptions for errors raised while handling circuits."""

from qbraid.exceptions import QBraidError


class CircuitError(QBraidError):
    """Base class for errors raised while processing a circuit."""

    pass

"""
Module defining exceptions for errors raised while handling circuits.

"""

from qbraid.exceptions import QbraidError


class CircuitConversionError(QbraidError):
    """Base class for errors raised while converting a circuit."""

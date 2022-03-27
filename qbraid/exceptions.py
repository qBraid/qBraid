"""Exceptions for errors raised by qBraid."""


class QbraidError(Exception):
    """Base class for errors raised by qBraid."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class UnsupportedCircuitError(QbraidError):
    """Base class for errors raised when processing unsupported circuits"""

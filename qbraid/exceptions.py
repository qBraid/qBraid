"""Exceptions for errors raised by qBraid."""

from typing import Optional


class QbraidError(Exception):
    """Base class for errors raised by qBraid."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)


class PackageError(QbraidError):
    """Raised when trying to use an unsuported package."""

    def __init__(self, package: Optional[str] = None, msg: Optional[str] = None) -> None:
        """Set the error message.
        Args:
            package: Name of unsupported package
            msg: Descriptive message, if any
        """

        message = []
        if package:
            message.append("{} is not a supported package".format(package))
        else:
            message.append("Package not supported")
        if msg:
            message.append(" {}.".format(msg))

        super().__init__(" ".join(message))

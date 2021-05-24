"""Exceptions for errors raised while processing a device."""


class DeviceError(Exception):
    """Base class for errors raised whioe processing a device."""

    def __init__(self, *message):
        """Set the error message."""
        super().__init__(" ".join(message))
        self.message = " ".join(message)

    def __str__(self):
        """Return the message."""
        return repr(self.message)
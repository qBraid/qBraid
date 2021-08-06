"""Exceptions for errors raised while processing a device."""

from qbraid.exceptions import QbraidError


class DeviceError(QbraidError):
    """Base class for errors raised while processing a device."""


class JobError(QbraidError):
    """Base class for errors raised by Jobs."""


class ConfigError(QbraidError):
    """Base class for errors raised while setting a user configuartion"""

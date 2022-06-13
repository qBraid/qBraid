"""
Module for exceptions raised while interacting with the qbraid API.

"""
from qbraid.exceptions import QbraidError


class ApiError(QbraidError):
    """Base class for errors raised in the :mod:`qbraid.api` module"""


class AuthError(ApiError):
    """Base class for errors raised authorizing user"""


class ConfigError(ApiError):
    """Base class for errors raised while setting a user configuartion"""


class RequestsApiError(ApiError):
    """Exception re-raising a RequestException."""

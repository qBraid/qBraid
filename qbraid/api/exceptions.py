from qbraid.exceptions import QbraidError


class AuthError(QbraidError):
    """Base class for errors raised authorizing user"""


class ConfigError(QbraidError):
    """Base class for errors raised while setting a user configuartion"""


class RequestsApiError(QbraidError):
    """Exception re-raising a RequestException."""

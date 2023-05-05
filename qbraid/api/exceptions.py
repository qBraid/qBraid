# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

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

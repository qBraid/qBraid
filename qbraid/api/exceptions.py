# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

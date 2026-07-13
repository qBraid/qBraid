# Copyright 2025 qBraid
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
Module defining exceptions for errors raised while processing a device.

"""

from typing import Optional

from qbraid.exceptions import QbraidError


class ProgramValidationError(QbraidError):
    """Base class for errors raised while validating a quantum program."""


class QbraidRuntimeError(QbraidError):
    """Base class for errors raised while submitting a quantum job."""


class ResourceNotFoundError(QbraidError):
    """Exception raised when the desired resource could not be found."""


class RuntimeAPIError(QbraidRuntimeError, ValueError):
    """Exception raised when a provider's REST API returns an error response.

    Carries the HTTP status code so callers can branch on the failure mode
    (e.g. distinguish "job doesn't exist" from "credentials rejected") instead
    of string-matching the exception message.

    Where the provider returns a structured error body, ``error_code`` holds the
    provider's own error identifier (finer-grained than the HTTP status) and
    ``trace`` the request id to quote in a support ticket. Both are None when the
    provider returned no structured error.

    Note: this also subclasses ``ValueError`` because these provider paths
    previously raised a bare ``ValueError``. Keeping that base means existing
    ``except ValueError`` code keeps working. It is transitional and can be
    dropped in a future major release.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        trace: Optional[str] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.trace = trace


class AuthorizationError(RuntimeAPIError):
    """Exception raised when provider credentials are missing, expired, or rejected.

    Corresponds to a 401/403 from the provider — the request was well-formed but
    the caller is not authenticated/authorized.
    """


class JobNotFoundError(RuntimeAPIError, ResourceNotFoundError):
    """Exception raised when the requested job/task does not exist (404).

    Inherits from :class:`ResourceNotFoundError` so existing handlers that catch
    that keep working, and from :class:`RuntimeAPIError` so callers get
    ``status_code`` and can catch every provider API error uniformly.
    """


class JobStateError(QbraidError):
    """Class for errors raised due to the state of a quantum job"""


class DeviceProgramTypeMismatchError(ProgramValidationError):
    """
    Exception raised when the program type does not match the Experiment type.

    """

    def __init__(self, program, expected_type, experiment_type):
        message = (
            f"Incompatible program type: '{type(program).__name__}'. "
            f"Experiment type '{experiment_type}' "
            f"requires a program of type '{expected_type}'."
        )
        super().__init__(message)

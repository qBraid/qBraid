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
from qbraid.exceptions import QbraidError


class ProgramValidationError(QbraidError):
    """Base class for errors raised while validating a quantum program."""


class QbraidRuntimeError(QbraidError):
    """Base class for errors raised while submitting a quantum job."""


class ResourceNotFoundError(QbraidError):
    """Exception raised when the desired resource could not be found."""


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

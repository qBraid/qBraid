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
Module defining all :mod:`~qbraid.runtime` enumerated types.

"""
from __future__ import annotations

from enum import IntEnum

from qbraid_core.services.runtime.schemas import DeviceStatus, JobStatus


class ValidationLevel(IntEnum):
    """Enumeration for program validation levels in qBraid runtime.

    Attributes:
        NONE (int): No validation is performed.
        WARN (int): Validation is performed, and warnings are issued if validation fails.
        RAISE (int): Validation is performed, and exceptions are raised if validation fails.
    """

    NONE = 0
    WARN = 1
    RAISE = 2


__all__ = ["ValidationLevel", "DeviceStatus", "JobStatus"]

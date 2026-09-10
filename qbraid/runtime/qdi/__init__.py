# Copyright 2026 qBraid
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
Module for submitting and managing jobs on any device that speaks the
Quantum Device Interface (QDI), whether through an in-process vendor client
or over the QDI HTTP binding.

.. currentmodule:: qbraid.runtime.qdi

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    QdiProvider
    QdiDevice
    QdiJob
    QdiHttpClient
    QdiClient
    QdiDeviceDescriptor

Data Types
-----------

.. autosummary::
   :toctree: ../stubs/

    QdiStatus
    QdiTaskStatus

Functions
----------

.. autosummary::
   :toctree: ../stubs/

    resolve_qdi_client

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

    QdiError
    QdiDeviceError
    QdiJobError

"""

from .client import QdiHttpClient, resolve_qdi_client
from .device import QdiDevice
from .exceptions import QdiDeviceError, QdiError, QdiJobError
from .job import QdiJob
from .protocol import QdiClient, QdiDeviceDescriptor, QdiStatus, QdiTaskStatus
from .provider import QdiProvider

__all__ = [
    "QdiClient",
    "QdiDevice",
    "QdiDeviceDescriptor",
    "QdiDeviceError",
    "QdiError",
    "QdiHttpClient",
    "QdiJob",
    "QdiJobError",
    "QdiProvider",
    "QdiStatus",
    "QdiTaskStatus",
    "resolve_qdi_client",
]

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
Module providing unified interface for interacting with
various quantum provider APIs.

.. currentmodule:: qbraid.providers

.. _devices_data_type:

Data Types
------------

.. autodata:: QDEVICE
   :annotation: = Type alias defining all supported quantum device / backend types

.. autosummary::
   :toctree: ../stubs/

   DeviceStatus
   DeviceType

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   QuantumDevice
   QuantumJob
   JobStatus
   QbraidProvider
   QuantumJobResult

Exceptions
------------

.. autosummary::
   :toctree: ../stubs/

   JobError
   JobStateError
   ProgramValidationError
   QbraidRuntimeError
   ResourceNotFoundError

"""
from ._import import QDEVICE, QDEVICE_LIBS, QDEVICE_TYPES, SUPPORTED_QDEVICES
from .device import QuantumDevice
from .enums import DeviceStatus, DeviceType, JobStatus
from .exceptions import (
    JobError,
    JobStateError,
    ProgramValidationError,
    QbraidRuntimeError,
    ResourceNotFoundError,
)
from .job import QuantumJob
from .provider import QbraidProvider
from .result import QuantumJobResult

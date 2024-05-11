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

.. currentmodule:: qbraid.runtime

.. _devices_data_type:

Data Types
------------

.. autosummary::
   :toctree: ../stubs/

   DeviceType
   DeviceStatus
   JobStatus


Classes
--------

.. autosummary::
   :toctree: ../stubs/

   QuantumDevice
   QuantumJob
   QuantumProvider
   QuantumJobResult
   RuntimeProfile
   QbraidProvider
   QbraidDevice
   QbraidJob
   QbraidJobResult
   ExperimentResult

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
import sys

from qbraid._import import LazyLoader

from .device import QbraidDevice, QuantumDevice
from .enums import DeviceStatus, DeviceType, JobStatus
from .exceptions import (
    JobError,
    JobStateError,
    ProgramValidationError,
    QbraidRuntimeError,
    ResourceNotFoundError,
)
from .job import QbraidJob, QuantumJob
from .profile import RuntimeProfile
from .provider import QbraidProvider, QuantumProvider
from .result import ExperimentResult, QbraidJobResult, QuantumJobResult

if "sphinx" in sys.modules:
    from . import aws, ibm
else:
    ibm = LazyLoader("ibm", globals(), "qbraid.runtime.ibm")
    aws = LazyLoader("aws", globals(), "qbraid.runtime.aws")

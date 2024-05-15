# Copyright (C) 2024 qBraid
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

.. _runtime_data_type:

Data Types
------------

.. autosummary::
   :toctree: ../stubs/

	DeviceType
	DeviceStatus
	JobStatus

Functions
------------

.. autosummary::
   :toctree: ../stubs/

	display_jobs_from_data

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   	TargetProfile
	QuantumDevice
	QuantumJob
	QuantumProvider
	QuantumJobResult

Exceptions
------------

.. autosummary::
   :toctree: ../stubs/

	JobStateError
	ProgramValidationError
	QbraidRuntimeError
	ResourceNotFoundError

"""
import sys

from qbraid._import import LazyLoader

from ._display import display_jobs_from_data
from .device import QuantumDevice
from .enums import DeviceStatus, DeviceType, JobStatus
from .exceptions import (
    JobStateError,
    ProgramValidationError,
    QbraidRuntimeError,
    ResourceNotFoundError,
)
from .job import QuantumJob
from .profile import TargetProfile
from .provider import QuantumProvider
from .result import QuantumJobResult

if "sphinx" in sys.modules:
    from . import braket, ionq, native, qiskit
else:
    native = LazyLoader("native", globals(), "qbraid.runtime.native")
    qiskit = LazyLoader("ibm", globals(), "qbraid.runtime.qiskit")
    braket = LazyLoader("braket", globals(), "qbraid.runtime.braket")
    ionq = LazyLoader("ionq", globals(), "qbraid.runtime.ionq")

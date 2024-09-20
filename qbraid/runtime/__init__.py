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

    ExperimentType
    DeviceStatus
    JobStatus
    NoiseModel

Functions
------------

.. autosummary::
   :toctree: ../stubs/

    display_jobs_from_data

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    Options
    TargetProfile
    QuantumDevice
    QuantumJob
    QuantumProvider
    Result
    ResultData
    GateModelResultData

Exceptions
------------

.. autosummary::
   :toctree: ../stubs/

    JobStateError
    ProgramValidationError
    QbraidRuntimeError
    ResourceNotFoundError
    DeviceProgramTypeMismatchError

"""
from . import native
from ._display import display_jobs_from_data
from .device import QuantumDevice
from .enums import DeviceStatus, ExperimentType, JobStatus, NoiseModel
from .exceptions import (
    DeviceProgramTypeMismatchError,
    JobStateError,
    ProgramValidationError,
    QbraidRuntimeError,
    ResourceNotFoundError,
)
from .job import QuantumJob
from .native import *
from .options import Options
from .profile import TargetProfile
from .provider import QuantumProvider
from .result import GateModelResultData, Result, ResultData

__all__ = [
    "QuantumDevice",
    "ExperimentType",
    "DeviceStatus",
    "JobStatus",
    "display_jobs_from_data",
    "JobStateError",
    "ProgramValidationError",
    "QbraidRuntimeError",
    "ResourceNotFoundError",
    "DeviceProgramTypeMismatchError",
    "TargetProfile",
    "QuantumJob",
    "QuantumProvider",
    "Options",
    "NoiseModel",
    "Result",
    "ResultData",
    "GateModelResultData",
]

__all__.extend(native.__all__)

_lazy_mods = ["azure", "braket", "ionq", "oqc", "qiskit"]


def __getattr__(name):
    if name in _lazy_mods:
        import importlib  # pylint: disable=import-outside-toplevel

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__ + _lazy_mods)

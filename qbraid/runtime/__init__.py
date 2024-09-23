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

    RuntimeOptions
    TargetProfile
    QuantumDevice
    QuantumJob
    QuantumProvider
    Result
    ResultData
    GateModelResultData
    AhsResultData
    AhsShotResult

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
from typing import TYPE_CHECKING

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
from .options import RuntimeOptions
from .profile import TargetProfile
from .provider import QuantumProvider
from .result import AhsResultData, AhsShotResult, GateModelResultData, Result, ResultData

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
    "RuntimeOptions",
    "NoiseModel",
    "Result",
    "ResultData",
    "GateModelResultData",
    "AhsResultData",
    "AhsShotResult",
]

__all__.extend(native.__all__)

_lazy_mods = ["aws", "azure", "ibm", "ionq", "oqc"]

_lazy_objs = {
    "aws": [
        "BraketProvider",
        "BraketDevice",
        "BraketQuantumTask",
    ],
    "azure": ["AzureQuantumProvider", "AzureQuantumDevice", "AzureQuantumJob"],
    "ionq": [
        "IonQSession",
        "IonQProvider",
        "IonQDevice",
        "IonQJob",
    ],
    "oqc": [
        "OQCProvider",
        "OQCDevice",
        "OQCJob",
    ],
    "ibm": [
        "QiskitRuntimeProvider",
        "QiskitBackend",
        "QiskitJob",
    ],
}

if TYPE_CHECKING:
    from .aws import BraketDevice as BraketDevice
    from .aws import BraketProvider as BraketProvider
    from .aws import BraketQuantumTask as BraketQuantumTask
    from .azure import AzureQuantumDevice as AzureQuantumDevice
    from .azure import AzureQuantumJob as AzureQuantumJob
    from .azure import AzureQuantumProvider as AzureQuantumProvider
    from .ibm import QiskitBackend as QiskitBackend
    from .ibm import QiskitJob as QiskitJob
    from .ibm import QiskitRuntimeProvider as QiskitRuntimeProvider
    from .ionq import IonQDevice as IonQDevice
    from .ionq import IonQJob as IonQJob
    from .ionq import IonQProvider as IonQProvider
    from .ionq import IonQSession as IonQSession
    from .oqc import OQCDevice as OQCDevice
    from .oqc import OQCJob as OQCJob
    from .oqc import OQCProvider as OQCProvider


def __getattr__(name):
    if name in _lazy_mods:
        import importlib  # pylint: disable=import-outside-toplevel

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module

    for mod_name, objects in _lazy_objs.items():
        if name in objects:
            import importlib  # pylint: disable=import-outside-toplevel

            module = importlib.import_module(f".{mod_name}", __name__)
            obj = getattr(module, name)
            globals()[name] = obj
            return obj

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(
        __all__ + _lazy_mods + [item for sublist in _lazy_objs.values() for item in sublist]
    )

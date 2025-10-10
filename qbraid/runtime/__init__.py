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
Module providing unified interface for interacting with
various quantum provider APIs.

.. currentmodule:: qbraid.runtime

.. _runtime_data_type:

Data Types
------------

.. autosummary::
   :toctree: ../stubs/

    DeviceStatus
    JobStatus
    NoiseModel
    NoiseModelSet
    ValidationLevel

Functions
------------

.. autosummary::
   :toctree: ../stubs/

    load_job
    get_providers
    load_provider
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
    AnnealingResultData

Exceptions
------------

.. autosummary::
   :toctree: ../stubs/

    JobStateError
    ProgramValidationError
    QbraidRuntimeError
    ResourceNotFoundError
    DeviceProgramTypeMismatchError
    JobLoaderError
    ProviderLoaderError

"""
import importlib
from typing import TYPE_CHECKING

from ._display import display_jobs_from_data
from .device import QuantumDevice
from .enums import DeviceStatus, JobStatus, ValidationLevel
from .exceptions import (
    DeviceProgramTypeMismatchError,
    JobStateError,
    ProgramValidationError,
    QbraidRuntimeError,
    ResourceNotFoundError,
)
from .job import QuantumJob
from .loader import JobLoaderError, ProviderLoaderError, get_providers, load_job, load_provider
from .noise import NoiseModel, NoiseModelSet
from .options import RuntimeOptions
from .profile import TargetProfile
from .provider import QuantumProvider
from .result import Result
from .result_data import (
    AhsResultData,
    AhsShotResult,
    AnnealingResultData,
    GateModelResultData,
    ResultData,
)

PROVIDERS = get_providers()

__all__ = [
    "QuantumDevice",
    "DeviceStatus",
    "JobStatus",
    "display_jobs_from_data",
    "load_job",
    "get_providers",
    "load_provider",
    "JobStateError",
    "ProgramValidationError",
    "QbraidRuntimeError",
    "ResourceNotFoundError",
    "DeviceProgramTypeMismatchError",
    "JobLoaderError",
    "ProviderLoaderError",
    "TargetProfile",
    "QuantumJob",
    "QuantumProvider",
    "RuntimeOptions",
    "NoiseModel",
    "NoiseModelSet",
    "Result",
    "ResultData",
    "GateModelResultData",
    "AhsResultData",
    "AhsShotResult",
    "AnnealingResultData",
    "ValidationLevel",
    "PROVIDERS",
]

_lazy = {
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
    "native": [
        "Session",
        "QbraidSession",
        "QbraidClient",
        "QbraidProvider",
        "QbraidDevice",
        "QbraidJob",
        "QirRunner",
    ],
    "schemas": [],
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
    from .native import QbraidClient as QbraidClient
    from .native import QbraidDevice as QbraidDevice
    from .native import QbraidJob as QbraidJob
    from .native import QbraidProvider as QbraidProvider
    from .native import QbraidSession as QbraidSession
    from .native import QirRunner as QirRunner
    from .native import Session as Session
    from .oqc import OQCDevice as OQCDevice
    from .oqc import OQCJob as OQCJob
    from .oqc import OQCProvider as OQCProvider


def __getattr__(name):
    for mod_name, objects in _lazy.items():
        if name == mod_name:
            module = importlib.import_module(f".{mod_name}", __name__)
            globals()[mod_name] = module
            return module

        if name in objects:
            module = importlib.import_module(f".{mod_name}", __name__)
            obj = getattr(module, name)
            globals()[name] = obj
            return obj

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(
        __all__ + list(_lazy.keys()) + [item for sublist in _lazy.values() for item in sublist]
    )

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
This top level module contains the main qBraid public functionality.

.. currentmodule:: qbraid

Functions
----------

.. autosummary::
   :toctree: ../stubs/

    about
    clear_cache
    cache_disabled

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QbraidError

"""
import importlib
from typing import TYPE_CHECKING

from ._about import about
from ._caching import cache_disabled, clear_cache
from ._version import __version__
from .exceptions import QbraidError

__all__ = [
    "about",
    "QbraidError",
    "__version__",
    "clear_cache",
    "cache_disabled",
]

_lazy = {
    "interface": [
        "circuits_allclose",
        "random_circuit",
    ],
    "passes": [],
    "programs": [
        "AnalogHamiltonianProgram",
        "GateModelProgram",
        "ProgramSpec",
        "Qasm2String",
        "Qasm3String",
        "QuantumProgram",
        "QPROGRAM",
        "QPROGRAM_NATIVE",
        "QPROGRAM_REGISTRY",
        "NATIVE_REGISTRY",
        "get_program_type_alias",
        "load_program",
        "register_program_type",
        "unregister_program_type",
        "ExperimentType",
    ],
    "runtime": [
        "AhsResultData",
        "AhsShotResult",
        "DeviceStatus",
        "GateModelResultData",
        "JobStatus",
        "NoiseModel",
        "QbraidProvider",
        "QbraidDevice",
        "QbraidJob",
        "QbraidSession",
        "QbraidClient",
        "QuantumDevice",
        "QuantumJob",
        "QuantumProvider",
        "Result",
        "ResultData",
        "RuntimeOptions",
        "Session",
        "TargetProfile",
    ],
    "transpiler": ["Conversion", "ConversionGraph", "ConversionScheme", "transpile", "translate"],
    "visualization": [],
}

if TYPE_CHECKING:
    from .interface import circuits_allclose as circuits_allclose
    from .interface import random_circuit as random_circuit
    from .programs import NATIVE_REGISTRY as NATIVE_REGISTRY
    from .programs import QPROGRAM as QPROGRAM
    from .programs import QPROGRAM_NATIVE as QPROGRAM_NATIVE
    from .programs import QPROGRAM_REGISTRY as QPROGRAM_REGISTRY
    from .programs import AnalogHamiltonianProgram as AnalogHamiltonianProgram
    from .programs import ExperimentType as ExperimentType
    from .programs import GateModelProgram as GateModelProgram
    from .programs import ProgramSpec as ProgramSpec
    from .programs import Qasm2String as Qasm2String
    from .programs import Qasm3String as Qasm3String
    from .programs import QuantumProgram as QuantumProgram
    from .programs import get_program_type_alias as get_program_type_alias
    from .programs import load_program as load_program
    from .programs import register_program_type as register_program_type
    from .programs import unregister_program_type as unregister_program_type
    from .runtime import AhsResultData as AhsResultData
    from .runtime import AhsShotResult as AhsShotResult
    from .runtime import DeviceStatus as DeviceStatus
    from .runtime import GateModelResultData as GateModelResultData
    from .runtime import JobStatus as JobStatus
    from .runtime import NoiseModel as NoiseModel
    from .runtime import QbraidClient as QbraidClient
    from .runtime import QbraidDevice as QbraidDevice
    from .runtime import QbraidJob as QbraidJob
    from .runtime import QbraidProvider as QbraidProvider
    from .runtime import QbraidSession as QbraidSession
    from .runtime import QuantumDevice as QuantumDevice
    from .runtime import QuantumJob as QuantumJob
    from .runtime import QuantumProvider as QuantumProvider
    from .runtime import Result as Result
    from .runtime import ResultData as ResultData
    from .runtime import RuntimeOptions as RuntimeOptions
    from .runtime import Session as Session
    from .runtime import TargetProfile as TargetProfile
    from .transpiler import Conversion as Conversion
    from .transpiler import ConversionGraph as ConversionGraph
    from .transpiler import ConversionScheme as ConversionScheme
    from .transpiler import translate as translate
    from .transpiler import transpile as transpile


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

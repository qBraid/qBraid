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
Module containing quantum circuit wrapper classes providing uniform
suite of methods and functionality for supported program types.

.. currentmodule:: qbraid.programs

.. _programs_data_type:

Data Types
-----------

.. data:: QPROGRAM_REGISTRY
   :type: dict[str, Type[Any]]
   :annotation: = Maps aliases of quantum program types to their respective Python type objects.

.. autosummary::
   :toctree: ../stubs/

    QbraidMetaType
    IonQDict
    QuboCoefficientsDict
    Qasm2String
    Qasm3String
    ExperimentType

Functions
----------

.. autosummary::
   :toctree: ../stubs/

    load_program
    get_program_type_alias
    get_qasm_type_alias
    register_program_type
    unregister_program_type

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    ProgramSpec
    QuantumProgram

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

    PackageValueError
    ProgramTypeError
    ValidationError
    QasmError
    TransformError
    ProgramLoaderError

"""
import importlib
from typing import TYPE_CHECKING

from ._import import NATIVE_REGISTRY
from .alias_manager import get_program_type_alias, get_qasm_type_alias
from .exceptions import (
    PackageValueError,
    ProgramTypeError,
    QasmError,
    TransformError,
    ValidationError,
)
from .experiment import ExperimentType
from .loader import ProgramLoaderError, load_program
from .program import QuantumProgram
from .registry import (
    QPROGRAM,
    QPROGRAM_ALIASES,
    QPROGRAM_NATIVE,
    QPROGRAM_REGISTRY,
    QPROGRAM_TYPES,
    derive_program_type_alias,
    register_program_type,
    unregister_program_type,
)
from .spec import ProgramSpec
from .typer import (
    IonQDict,
    Qasm2String,
    Qasm2StringType,
    Qasm3String,
    Qasm3StringType,
    QbraidMetaType,
    QuboCoefficientsDict,
)

__all__ = [
    "NATIVE_REGISTRY",
    "PackageValueError",
    "ProgramSpec",
    "ProgramTypeError",
    "TransformError",
    "ProgramLoaderError",
    "QPROGRAM",
    "QPROGRAM_ALIASES",
    "QPROGRAM_NATIVE",
    "QPROGRAM_REGISTRY",
    "QPROGRAM_TYPES",
    "QasmError",
    "QuantumProgram",
    "derive_program_type_alias",
    "get_program_type_alias",
    "load_program",
    "get_qasm_type_alias",
    "register_program_type",
    "unregister_program_type",
    "ValidationError",
    "QbraidMetaType",
    "IonQDict",
    "QuboCoefficientsDict",
    "Qasm2String",
    "Qasm3String",
    "Qasm2StringType",
    "Qasm3StringType",
    "ExperimentType",
]

_lazy = {
    "gate_model": ["GateModelProgram"],
    "ahs": ["AnalogHamiltonianProgram", "AHSEncoder"],
    "annealing": ["AnnealingProgram", "ProblemEncoder", "ProblemType", "Problem", "QuboProblem"],
}

if TYPE_CHECKING:
    from .ahs import AHSEncoder as AHSEncoder
    from .ahs import AnalogHamiltonianProgram as AnalogHamiltonianProgram
    from .annealing import AnnealingProgram as AnnealingProgram
    from .annealing import Problem as Problem
    from .annealing import ProblemEncoder as ProblemEncoder
    from .annealing import ProblemType as ProblemType
    from .annealing import QuboProblem as QuboProblem
    from .gate_model import GateModelProgram as GateModelProgram


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

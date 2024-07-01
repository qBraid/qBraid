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
Module containing quantum circuit wrapper classes providing uniform
suite of methods and functionality for supported program types.

.. currentmodule:: qbraid.programs

.. _programs_data_type:

Data Types
-----------

.. data:: QPROGRAM_REGISTRY
   :type: dict[str, Type[Any]]
   :annotation: = Maps aliases of quantum program types to their respective Python type objects.

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   load_program
   get_program_type_alias
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
   QasmError
   TransformError

"""
from ._import import NATIVE_REGISTRY
from .alias_manager import get_program_type_alias, parse_qasm_type_alias
from .exceptions import PackageValueError, ProgramTypeError, QasmError, TransformError
from .loader import load_program
from .program import QuantumProgram
from .registry import (
    QPROGRAM,
    QPROGRAM_ALIASES,
    QPROGRAM_REGISTRY,
    QPROGRAM_TYPES,
    derive_program_type_alias,
    register_program_type,
    unregister_program_type,
)
from .spec import ProgramSpec

__all__ = [
    "NATIVE_REGISTRY",
    "PackageValueError",
    "ProgramSpec",
    "ProgramTypeError",
    "TransformError",
    "QPROGRAM",
    "QPROGRAM_ALIASES",
    "QPROGRAM_REGISTRY",
    "QPROGRAM_TYPES",
    "QasmError",
    "QuantumProgram",
    "derive_program_type_alias",
    "get_program_type_alias",
    "load_program",
    "parse_qasm_type_alias",
    "register_program_type",
    "unregister_program_type",
]

_lazy_mods = ["circuits", "ahs"]


def __getattr__(name):
    if name in _lazy_mods:
        import importlib  # pylint: disable=import-outside-toplevel

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__ + _lazy_mods)

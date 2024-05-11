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

.. autodata:: QPROGRAM
   :annotation: = Type alias defining all supported quantum circuit / program types

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   load_program
   get_program_type_alias
   register_program_type

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   ProgramSpec
   QuantumProgram
   QbraidProgram

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   PackageValueError
   ProgramTypeError
   QasmError

"""
from ._import import NATIVE_REGISTRY
from .alias_manager import get_program_type_alias, parse_qasm_type_alias
from .exceptions import PackageValueError, ProgramTypeError, QasmError
from .loader import load_program
from .program import QbraidProgram, QuantumProgram
from .registry import (
    QPROGRAM,
    QPROGRAM_ALIASES,
    QPROGRAM_REGISTRY,
    QPROGRAM_TYPES,
    derive_program_type_alias,
    register_program_type,
)
from .spec import ProgramSpec

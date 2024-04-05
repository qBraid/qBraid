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

   get_qasm_version
   get_program_type
   load_program
   remove_qasm_barriers
   unfold_qasm_gate_defs
   flatten_qasm_program
   decompose_qasm_qelib1

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   QuantumProgram

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   PackageValueError
   ProgramTypeError
   QasmError

"""
from ._import import QPROGRAM, QPROGRAM_LIBS, QPROGRAM_TYPES, SUPPORTED_QPROGRAMS
from .abc_program import QuantumProgram
from .exceptions import PackageValueError, ProgramTypeError, QasmError
from .inspector import get_program_type, get_qasm_version
from .loader import load_program
from .qasm_passes import flatten_qasm_program, remove_qasm_barriers, unfold_qasm_gate_defs
from .qasm_qelib1 import decompose_qasm_qelib1

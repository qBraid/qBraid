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
Module for appyling transformations to OpenQASM 2 programs.

.. currentmodule:: qbraid.passes.qasm2

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   remove_qasm_barriers
   unfold_qasm_gate_defs
   flatten_qasm_program
   decompose_qasm2

"""
from .compat import flatten_qasm_program, remove_qasm_barriers, unfold_qasm_gate_defs
from .decompose import decompose_qasm2

__all__ = [
    "flatten_qasm_program",
    "remove_qasm_barriers",
    "unfold_qasm_gate_defs",
    "decompose_qasm2",
]

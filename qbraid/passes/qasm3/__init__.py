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
Module for appyling transformations to OpenQASM 3 programs.

.. currentmodule:: qbraid.passes.qasm3

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   rebase
   decompose_qasm3
   insert_gate_def
   replace_gate_name
   add_stdgates_include
   remove_stdgates_include
   convert_qasm_pi_to_decimal
   normalize_qasm_gate_params
   remove_unused_gates

"""
from .compat import (
    add_stdgates_include,
    convert_qasm_pi_to_decimal,
    insert_gate_def,
    normalize_qasm_gate_params,
    remove_stdgates_include,
    replace_gate_name,
)
from .decompose import decompose_qasm3, rebase
from .format import remove_unused_gates

__all__ = [
    "rebase",
    "decompose_qasm3",
    "insert_gate_def",
    "replace_gate_name",
    "add_stdgates_include",
    "remove_stdgates_include",
    "convert_qasm_pi_to_decimal",
    "normalize_qasm_gate_params",
    "remove_unused_gates",
]

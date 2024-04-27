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
Module containing functions for working with quantum programs in QASM format.

.. currentmodule:: qbraid.transforms.qasm2

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   remove_qasm_barriers
   unfold_qasm_gate_defs
   flatten_qasm_program
   decompose_qasm_qelib1
   convert_qasm_pi_to_decimal

"""
from .passes import (
    convert_qasm_pi_to_decimal,
    flatten_qasm_program,
    remove_qasm_barriers,
    unfold_qasm_gate_defs,
)
from .qasm_qelib1 import decompose_qasm_qelib1

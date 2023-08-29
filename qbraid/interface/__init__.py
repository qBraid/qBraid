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
===============================================
Interface (:mod:`qbraid.interface`)
===============================================

.. currentmodule:: qbraid.interface

.. autosummary::
   :toctree: ../stubs/

   to_unitary
   unitary_to_little_endian
   random_unitary_matrix
   convert_to_contiguous
   circuits_allclose
   random_circuit
   circuit_drawer
   rev_qubits_unitary
   ContiguousConversionError
   UnitaryCalculationError

"""
from .calculate_unitary import (
    UnitaryCalculationError,
    circuits_allclose,
    random_unitary_matrix,
    rev_qubits_unitary,
    to_unitary,
    unitary_to_little_endian,
)
from .circuit_drawer import circuit_drawer
from .convert_to_contiguous import ContiguousConversionError, convert_to_contiguous
from .random_circuit import random_circuit

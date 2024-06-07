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
Module for generaing random quantum circuits and unitary matrices
for testing.

.. currentmodule:: qbraid.interface.random

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   random_circuit
   random_unitary_matrix

"""
from .random import random_circuit, random_unitary_matrix

__all__ = ["random_circuit", "random_unitary_matrix"]

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
Module containing functions for transforming cirq programs.

.. currentmodule:: qbraid.transforms.cirq

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   decompose
   map_zpow_and_unroll

"""
from .passes import decompose, map_zpow_and_unroll

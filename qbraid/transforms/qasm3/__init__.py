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

.. currentmodule:: qbraid.transforms.qasm3

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   transform_notation_to_external
   transform_notation_from_external


"""
from .compat import transform_notation_from_external, transform_notation_to_external

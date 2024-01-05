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
Module for compiling programs targeted at Amazon Braket
supported devices.

.. currentmodule:: qbraid.compiler.braket

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   braket_ionq_compile

"""
from .ionq import braket_ionq_compile

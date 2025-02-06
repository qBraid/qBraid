# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
CUDA-Q conversions

.. currentmodule:: qbraid.transpiler.conversions.cudaq

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   cudaq_to_qasm2
   cudaq_to_pyqir

"""
from .cudaq_extras import cudaq_to_pyqir
from .cudaq_to_qasm2 import cudaq_to_qasm2

__all__ = ["cudaq_to_qasm2", "cudaq_to_pyqir"]

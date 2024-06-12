# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: skip-file

"""
Mdule submiting and managing quantm tasks through AWS
and Amazon Braket supported devices.

.. currentmodule:: qbraid.runtime.braket

Classes
---------

.. autosummary::
   :toctree: ../stubs/

   BraketDevice
   BraketProvider
   BraketQuantumTask
   BraketGateModelJobResult
   BraketAhsJobResult

Functions
-----------

.. autosummary::
   :toctree: ../stubs/

   get_quantum_task_cost

"""
from .device import BraketDevice
from .job import BraketQuantumTask
from .provider import BraketProvider
from .result import BraketAhsJobResult, BraketGateModelJobResult
from .tracker import get_quantum_task_cost

__all__ = [
    "BraketDevice",
    "BraketProvider",
    "BraketQuantumTask",
    "BraketGateModelJobResult",
    "BraketAhsJobResult",
    "get_quantum_task_cost",
]

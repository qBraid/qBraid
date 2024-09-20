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
Module for submitting and managing jobs through the Azure Quantum API.

.. currentmodule:: qbraid.runtime.azure

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    AzureQuantumProvider
    AzureQuantumDevice
    AzureQuantumJob

"""
from .device import AzureQuantumDevice
from .job import AzureQuantumJob
from .provider import AzureQuantumProvider

__all__ = [
    "AzureQuantumProvider",
    "AzureQuantumDevice",
    "AzureQuantumJob",
]

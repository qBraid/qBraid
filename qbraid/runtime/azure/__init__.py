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
Mdule submiting and managing jobs through the Azure Quantum API.

.. currentmodule:: qbraid.runtime.azure

Classes
--------

.. autosummary::
   :toctree: ../stubs/

	AzureSession
	AzureQuantumProvider
    AzureQuantumDevice

"""
from .device import AzureQuantumDevice
from .provider import AzureQuantumProvider, AzureSession

__all__ = ["AzureSession", "AzureQuantumProvider", "AzureQuantumDevice"]
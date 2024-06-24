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
Module defining IQM provider class

"""
from iqm.iqm_client import IQMClient

from qbraid.runtime.provider import QuantumProvider

from .device import IQMDevice

class IQMProvider(QuantumProvider):
    """IQM provider class."""

    def __init__(self, url):
        super().__init__()
        self.client = IQMClient(url)

    def get_devices(self, **kwargs):
        """Get all IQM devices."""
        raise NotImplementedError
    
    def get_device(self, device_id: str):
        """Get an IQM device."""
        raise NotImplementedError   
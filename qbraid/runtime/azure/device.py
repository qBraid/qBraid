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
Module defining Azure Quantum device class

"""
from typing import TYPE_CHECKING

from qbraid.runtime.device import QuantumDevice

if TYPE_CHECKING:
    import qbraid.runtime
    from qbraid.runtime.azure.provider import AzureSession


class AzureQuantumDevice(QuantumDevice):
    """Azure quantum device interface."""

    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        session: "qbraid.runtime.azure.provider.AzureSession",
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> "qbraid.runtime.azure.provider.AzureSession":
        """Return the Azure session."""
        return self._session

    def status(self) -> "qbraid.runtime.DeviceStatus":
        """Return the current status of the Azure device."""
        device_data = self.session.get_device(self.id)

        return device_data.get("status")

    def submit(self, run_input, name, provider, backend, qubits, **kwargs): # pylint: disable=too-many-arguments
        """Submit a job to the Azure device."""
        # is_single_input = not isinstance(run_input, list)
        # run_input = [run_input] if is_single_input else run_input

        job = self._session.create_job(run_input, name, provider, backend, qubits)
        return job

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
Module defining Azure Quantum device class for all devices managed by Azure Quantum.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import AzureQuantumJob

if TYPE_CHECKING:
    import azure.quantum

    import qbraid.programs
    import qbraid.runtime


class AzureQuantumDevice(QuantumDevice):
    """Azure quantum device interface."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        workspace: azure.quantum.Workspace,
    ):
        super().__init__(profile=profile)
        self._workspace = workspace
        self._device = self.workspace.get_targets(name=self.id)

    @property
    def workspace(self) -> azure.quantum.Workspace:
        """Return the Azure Quantum Workspace."""
        return self._workspace

    def status(self) -> qbraid.runtime.enums.DeviceStatus:
        """Return the current status of the Azure device.

        Returns:
            DeviceStatus: The current status of the device.
        """
        status = self._device._current_availability
        status_map = {
            "Available": DeviceStatus.ONLINE,
            "Deprecated": DeviceStatus.UNAVAILABLE,
            "Unavailable": DeviceStatus.OFFLINE,
        }
        return status_map.get(status, DeviceStatus.UNAVAILABLE)

    def submit(self, run_input: qbraid.programs.QPROGRAM, *args, **kwargs) -> AzureQuantumJob:
        """Submit a job to the Azure device.

        Args:
            run_input (Any): The program to submit.

        Returns:
            AzureQuantumJob: The submitted job.
        """
        if isinstance(run_input, list):
            raise ValueError(
                "Batch jobs (list of inputs) are not supported for this device. "
                "Please provide a single job input."
            )

        job = self._device.submit(run_input, *args, **kwargs)
        return AzureQuantumJob(job_id=job.id, workspace=self.workspace, device=self)

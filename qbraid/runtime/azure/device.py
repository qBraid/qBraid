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

from typing import TYPE_CHECKING, Any

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import AzureJob

if TYPE_CHECKING:
    import qbraid.runtime
    import qbraid.runtime.azure


class AzureQuantumDevice(QuantumDevice):
    """Azure quantum device interface."""

    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        client: "qbraid.runtime.azure.AzureClient",
    ):
        super().__init__(profile=profile)
        self._client = client

    @property
    def client(self) -> "qbraid.runtime.azure.AzureClient":
        """Return the Azure session."""
        return self._client

    def status(self) -> "qbraid.runtime.enums.DeviceStatus":
        """Return the current status of the Azure device.

        Returns: DeviceStatus: The current status of the device.
        """
        device_data = self.client.get_device(self.id)
        status = device_data["_current_availability"]
        status_map = {
            "Available": DeviceStatus.ONLINE,
            "Deprecated": DeviceStatus.UNAVAILABLE,
            "Unavailable": DeviceStatus.OFFLINE,
        }
        return status_map.get(status, DeviceStatus.UNAVAILABLE)

    # pylint:disable=arguments-differ
    def submit(self, program: Any, job_name: str, shots: int = 100) -> AzureJob:
        """Submit a job to the Azure device.

        Args: program (Any): The program to submit.
              job_name (str): The name of the job.
              shots (int): The number of shots to run.

        Returns: AzureJob: The submitted job.
        """

        if isinstance(program, list):
            raise ValueError(
                "Batch jobs (list of inputs) are not supported for this device. "
                "Please provide a single job input."
            )

        job = self.client.submit_job(
            {"device_name": self.id, "program": program, "job_name": job_name, "shots": shots}
        )

        return AzureJob(job_id=job.id, client=self.client, device=self)

# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

    def __str__(self):
        """String representation of the AzureQuantumDevice object."""
        return f"{self.__class__.__name__}('{self._device.name}')"

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
            "Degraded": DeviceStatus.OFFLINE,
        }
        return status_map.get(status, DeviceStatus.UNAVAILABLE)

    def is_available(self) -> bool:
        """Check if the Azure device is available for use.

        Returns:
            bool: True if the device is available, False otherwise.
        """
        current_status = self.status()
        if current_status == DeviceStatus.ONLINE:
            return True
        return False

    def submit(
        self, run_input: qbraid.programs.QPROGRAM | list(qbraid.programs.QPROGRAM), *args, **kwargs
    ) -> AzureQuantumJob | list(AzureQuantumJob):
        """Submit a job to the Azure device.

        Args:
            run_input (Any): The program to submit.

        Returns:
            AzureQuantumJob: The submitted job.
        """
        if isinstance(run_input, list):
            quantum_jobs = []
            for _, qprogram in enumerate(run_input):
                job = self._device.submit(qprogram, *args, **kwargs)
                quantum_jobs.append(
                    AzureQuantumJob(job_id=job.id, workspace=self.workspace, device=self)
                )
            return quantum_jobs

        job = self._device.submit(run_input, *args, **kwargs)
        return AzureQuantumJob(job_id=job.id, workspace=self.workspace, device=self)

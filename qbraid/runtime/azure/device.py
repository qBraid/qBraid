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

from typing import TYPE_CHECKING, Optional

from qbraid.programs import load_program
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
        """Return the current status of the Azure device."""
        device_data = self.client.get_device(self.id)
        status = device_data["status"]
        status_map = {
            "Available": DeviceStatus.ONLINE,
            "Deprecated": DeviceStatus.UNAVAILABLE,
            "Unavailable": DeviceStatus.OFFLINE,
        }
        return status_map.get(status, DeviceStatus.UNAVAILABLE)

    def submit(
        self, run_input: str, *args, shots: int = 100, name: Optional[str] = None, **kwargs
    ) -> AzureJob:
        """Submit a job to the Azure device."""

        if isinstance(run_input, list):
            raise ValueError(
                "Batch jobs (list of inputs) are not supported for this device. "
                "Please provide a single job input."
            )

        provider = self.profile.get("provider_name")
        storage_data = self.client.create_job_storage(run_input, "application/qasm")
        name = name or f"{provider}-job"

        job_id = storage_data["id"]
        container_sas_uri = storage_data["containerUri"]
        input_sas_uri = storage_data["inputDataUri"]
        output_sas_uri = storage_data["outputDataUri"]

        formats = {"quantinuum": ["honeywell.openqasm.v1", "honeywell.quantum-results.v1"]}
        input_data_format, output_data_format = formats[provider]

        program = load_program(run_input)
        num_qubits = program.num_qubits

        payload = self.create_payload(
            container_sas_uri,
            input_sas_uri,
            output_sas_uri,
            job_id,
            job_name=name,
            input_data_format=input_data_format,
            provider=provider,
            backend=self.id,
            num_qubits=num_qubits,
            num_shots=shots,
            total_count=100,
            output_data_format=output_data_format,
        )

        self.client.submit_job(payload)

        return AzureJob(job_id=job_id, client=self.client, device=self)

    @staticmethod
    def create_payload(  # pylint: disable=too-many-arguments
        container_uri: str,
        input_uri: str,
        output_uri: str,
        job_id: str,
        job_name: str,
        input_data_format: str,
        provider: str,
        backend: str,
        num_qubits: str,
        num_shots: int,
        total_count: int,
        output_data_format: str,
    ) -> dict:
        """Create the payload for the job."""
        payload = {
            "containerUri": container_uri,
            "id": job_id,
            "inputDataFormat": input_data_format,  # "honeywell.openqasm.v1"
            "itemType": "Job",
            "name": job_name,
            "providerId": provider,
            "target": backend,  # changeable
            "metadata": {
                "qiskit": "True",
                "name": job_name,
                "num_qubits": num_qubits,
                "metadata": "null",
                "meas_map": "[0]",
            },
            "inputDataUri": input_uri,
            "inputParams": {"shots": num_shots, "count": total_count},
            "outputDataFormat": output_data_format,  # "honeywell.quantum-results.v1"
            "outputDataUri": output_uri,
        }

        return payload

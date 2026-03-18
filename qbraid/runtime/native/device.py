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

# pylint: disable=arguments-differ

"""
Module defining QbraidDevice class

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbraid_core.services.runtime import QuantumRuntimeClient
from qbraid_core.services.runtime.schemas import JobRequest, Program

from qbraid._logging import logger
from qbraid.runtime.batch import get_active_batch, get_active_batch_session
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.noise import NoiseModel

from .job import QbraidJob

if TYPE_CHECKING:
    import qbraid_core.services.runtime

    import qbraid.runtime


class QbraidDevice(QuantumDevice):
    """Class to represent a qBraid device."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        client: qbraid_core.services.runtime.QuantumRuntimeClient | None = None,
        **kwargs,
    ):
        """Create a new QbraidDevice object."""
        super().__init__(profile=profile, **kwargs)
        self._client = client or QuantumRuntimeClient()

    @property
    def client(self) -> QuantumRuntimeClient:
        """Return the QuantumClient object."""
        return self._client

    def __str__(self):
        """String representation of the QbraidDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> qbraid.runtime.DeviceStatus:
        """Return device status."""
        device_data = self.client.get_device(self.id)
        return device_data.status

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""
        device_data = self.client.get_device(self.id)
        return device_data.queueDepth or 0

    def _resolve_noise_model(self, noise_model: NoiseModel | str) -> str:
        """Verify given noise model is supported by device and map to string representation."""
        if self.profile.noise_models is None:
            raise ValueError("Noise models are not supported by this device.")

        if isinstance(noise_model, NoiseModel):
            noise_model = noise_model.value
        elif not isinstance(noise_model, str):
            raise ValueError(
                f"Invalid type for noise model: {type(noise_model)}. Expected str or NoiseModel."
            )

        if noise_model not in self.profile.noise_models:
            raise ValueError(f"Noise model '{noise_model}' not supported by device.")

        return self.profile.noise_models.get(noise_model).name

    # pylint: disable-next=too-many-arguments
    def submit(
        self,
        run_input: Program | list[Program],
        shots: int | None = None,
        name: str | None = None,
        tags: dict[str, str | int | bool] | None = None,
        runtime_options: dict[str, Any] | None = None,
        **kwargs,
    ) -> QbraidJob | list[QbraidJob]:
        """Submit a program to the device.

        If an active BatchJobSession context exists, the batch QRN is
        automatically included in the job request and submitted jobs
        are registered with the session.
        """
        tags = tags or {}
        runtime_options = runtime_options or {}
        noise_model: NoiseModel | str | None = runtime_options.pop("noise_model", None)

        # Read batch context — only QbraidDevice supports batched execution
        batch_job_qrn = get_active_batch()

        if noise_model:
            runtime_options["noiseModel"] = self._resolve_noise_model(noise_model)

        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input

        if batch_job_qrn:
            logger.debug("Submitting job to device '%s' (batch: %s)", self.id, batch_job_qrn)

        jobs = []

        for program in run_input:
            job_request = JobRequest(
                deviceQrn=self.id,
                program=program,
                shots=shots,
                name=name,
                tags=tags,
                runtimeOptions=runtime_options,
                batchJobQrn=batch_job_qrn,
            )
            job_data = self.client.create_job(job_request)
            jobs.append(QbraidJob(job_id=job_data.jobQrn, device=self, client=self.client))

        result = jobs[0] if is_single_input else jobs

        # Register submitted jobs with the active batch session
        if batch_job_qrn:
            session = get_active_batch_session()
            if session is not None:
                for job in jobs:
                    session._register_job(job)

        return result

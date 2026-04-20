# Copyright 2026 qBraid
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
Module defining OriginQ device class.

"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.profile import TargetProfile

from .job import OriginJob

if TYPE_CHECKING:
    from pyqpanda3.core import QProg
    from pyqpanda3.qcloud import QCloudBackend, QCloudService

logger = logging.getLogger(__name__)


class OriginDeviceError(QbraidRuntimeError):
    """Exception raised by OriginDevice."""


class OriginDevice(QuantumDevice):
    """OriginQ QCloud device interface."""

    def __init__(
        self,
        profile: TargetProfile,
        service: QCloudService,
        backend: QCloudBackend | None = None,
        **kwargs,
    ):
        super().__init__(profile=profile, **kwargs)
        self._service = service
        self._backend = backend

    @property
    def service(self) -> QCloudService:
        """Return the underlying QCloudService."""
        return self._service

    @property
    def backend(self) -> QCloudBackend:
        """Return the underlying QCloudBackend."""
        if self._backend is None:
            self._backend = self.service.backend(self.id)
        return self._backend

    def __str__(self):
        """String representation of the OriginDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the current status of the OriginQ device."""
        catalog = self.service.backends()
        for backend_id, available in catalog.items():
            if backend_id == self.id:
                return DeviceStatus.ONLINE if available else DeviceStatus.OFFLINE
        raise OriginDeviceError(f"Device '{self.id}' not found in service catalog.")

    def _submit_single(self, run_input: QProg, shots: int) -> OriginJob:
        """Submit a single quantum program."""
        backend = self.backend

        if self.profile.simulator:
            qcloud_job = backend.run(run_input, shots)
        else:
            # pylint: disable-next=import-outside-toplevel
            from pyqpanda3.qcloud import QCloudOptions

            options = QCloudOptions()
            qcloud_job = backend.run(run_input, shots, options)

        return OriginJob(
            job_id=qcloud_job.job_id(),
            device=self,
            job=qcloud_job,
            service=self.service,
        )

    def submit(  # pylint: disable=arguments-differ
        self, run_input: QProg | list[QProg], shots: int
    ) -> OriginJob | list[OriginJob]:
        """Submit a quantum program or list of programs to the OriginQ device.

        For simulator backends, batch input (``list[QProg]``) is submitted as
        individual jobs since the pyqpanda3 SDK only supports batch submission
        on hardware (QPU) backends.

        For QPU backends, batch input is submitted as a single job via the SDK's
        native batch API.
        """
        if not isinstance(run_input, list):
            return self._submit_single(run_input, shots)

        # Simulator: fan out to individual jobs (SDK only supports native batch on QPU)
        if self.profile.simulator:
            return [self._submit_single(prog, shots) for prog in run_input]

        # QPU: single job containing all programs
        # pylint: disable-next=import-outside-toplevel
        from pyqpanda3.qcloud import QCloudOptions

        options = QCloudOptions()
        qcloud_job = self.backend.run(run_input, shots, options)

        return OriginJob(
            job_id=qcloud_job.job_id(),
            device=self,
            job=qcloud_job,
            service=self.service,
        )

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
Module defining OriginQ device class.

"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import OriginJob

if TYPE_CHECKING:
    from pyqpanda3.core import QProg
    from pyqpanda3.qcloud import QCloudBackend, QCloudService

logger = logging.getLogger(__name__)

SIMULATOR_BACKENDS: dict[str, int] = {
    "full_amplitude": 35,
    "partial_amplitude": 68,
    "single_amplitude": 200,
}


class OriginDevice(QuantumDevice):
    """OriginQ QCloud device interface."""

    def __init__(
        self,
        profile,
        backend: QCloudBackend,
        backend_name: str,
        service: Optional[QCloudService] = None,
    ):
        super().__init__(profile=profile)
        self._backend = backend
        self._backend_name = backend_name
        self._service = service

    @property
    def backend(self) -> Any:
        """Return the underlying QCloudBackend."""
        return self._backend

    @property
    def backend_name(self) -> str:
        """Return the OriginQ backend name."""
        return self._backend_name

    def status(self) -> DeviceStatus:
        """Return the current status of the OriginQ device."""
        # OriginQ does not expose health endpoints; assume online when instantiated.
        return DeviceStatus.ONLINE

    def submit(
        self, run_input: Union[QProg, list[QProg]], *, shots: int, **kwargs
    ) -> Union[OriginJob, list[OriginJob]]:
        """Submit a quantum program or list of programs to the OriginQ device."""
        is_single = not isinstance(run_input, (list, Sequence))
        inputs = [run_input] if is_single else run_input

        jobs = []
        for qprog in inputs:
            nshots = int(shots)

            if self._backend_name in SIMULATOR_BACKENDS:
                backend_job = self._backend.run(qprog, nshots)
            else:
                # pylint: disable-next=import-outside-toplevel
                from pyqpanda3 import qcloud as qcloud_module

                options = qcloud_module.QCloudOptions()
                backend_job = self._backend.run(qprog, nshots, options)

            job_id = backend_job.job_id()
            jobs.append(
                OriginJob(
                    job_id=job_id,
                    device=self,
                    backend_job=backend_job,
                    service=self._service,
                )
            )

        return jobs[0] if is_single else jobs

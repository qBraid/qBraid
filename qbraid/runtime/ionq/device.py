# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=invalid-name

"""
Module defining IonQ device class

"""
from typing import TYPE_CHECKING

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import IonQJob

if TYPE_CHECKING:
    import qbraid.runtime
    import qbraid.runtime.ionq.provider


class IonQDevice(QuantumDevice):
    """IonQ quantum device interface."""

    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        session: "qbraid.runtime.ionq.provider.IonQSession",
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> "qbraid.runtime.ionq.provider.IonQSession":
        """Return the IonQ session."""
        return self._session

    def status(self) -> "qbraid.runtime.DeviceStatus":
        """Return the current status of the IonQ device."""
        device_data = self.session.get_device(self.id)
        status = device_data.get("status")

        if status in ["available", "running"]:
            return DeviceStatus.ONLINE

        if status in ["unavailable", "reserved", "calibrating"]:
            return DeviceStatus.UNAVAILABLE

        if status == "offline":
            return DeviceStatus.OFFLINE

        raise ValueError(f"Unrecognized device status: {status}")

    def submit(self, run_input: list[str], *args, shots: int = 100, **kwargs) -> IonQJob:
        """Submit a job to the IonQ device."""
        data = {
            "target": self.id,
            "shots": shots,
            "input": {"format": "openqasm", "data": run_input},
            **kwargs,
        }
        job_data = self.session.create_job(data)
        job_id = job_data.get("id")
        return IonQJob(job_id=job_id, session=self.session, device=self)

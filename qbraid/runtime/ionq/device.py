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
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Union

from qbraid.programs.circuits.qasm import OpenQasm2Program
from qbraid.programs.typer import Qasm2StringType
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.transpiler.conversions.qasm2 import qasm2_to_ionq

from .job import IonQJob

if TYPE_CHECKING:
    import qbraid.runtime
    import qbraid.runtime.ionq.provider


class IonQDevice(QuantumDevice):
    """IonQ quantum device interface."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        session: qbraid.runtime.ionq.provider.IonQSession,
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> qbraid.runtime.ionq.provider.IonQSession:
        """Return the IonQ session."""
        return self._session

    def status(self) -> qbraid.runtime.DeviceStatus:
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

    def transform(self, run_input: Qasm2StringType) -> dict[str, Union[int, list[dict[str, Any]]]]:
        """Transform the input to the IonQ device."""
        program = OpenQasm2Program(run_input)
        program.transform(device=self)
        ionq_program = qasm2_to_ionq(program.program)
        return ionq_program

    # pylint:disable-next=arguments-differ
    def submit(self, run_input: list[dict], shots: int = 100, **kwargs) -> IonQJob:
        """Submit a job to the IonQ device."""
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        jobs = []
        for input_data in run_input:
            data = {
                "target": self.id,
                "shots": shots,
                "input": input_data,
                **kwargs,
            }
            serialized_data = json.dumps(data)
            job_data = self.session.create_job(serialized_data)
            job_id = job_data.get("id")
            if not job_id:
                raise ValueError("Job ID not found in the response")
            qbraid_job = IonQJob(job_id=job_id, session=self.session, device=self, shots=shots)
            jobs.append(qbraid_job)
        return jobs[0] if is_single_input else jobs

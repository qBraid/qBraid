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
Module defining IonQ device class

"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

from qbraid.programs import load_program
from qbraid.programs.typer import QasmStringType
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

        if status == "retired":
            return DeviceStatus.RETIRED

        if status == "offline":
            return DeviceStatus.OFFLINE

        raise ValueError(f"Unrecognized device status: {status}")

    def avg_queue_time(self) -> int:
        """Return the average queue time for the IonQ device."""
        device_data = self.session.get_device(self.id)
        return device_data["average_queue_time"]

    def transform(self, run_input: QasmStringType) -> QasmStringType:
        """Transform the input to the IonQ device."""
        program = load_program(run_input)
        program.transform(device=self)
        return program.program

    # pylint:disable-next=arguments-differ,too-many-arguments
    def submit(
        self,
        run_input: list[dict[str, Any]],
        shots: int,
        preflight: bool = False,
        name: Optional[str] = None,
        noise: Optional[dict[str, Any]] = None,
        error_mitigation: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> IonQJob:
        """Submit a job to the IonQ device."""
        is_single_input = not isinstance(run_input, list)
        job_data = {
            "target": self.id,
            "shots": shots,
            "preflight": preflight,
            **kwargs,
        }
        optional_fields = {
            "name": name,
            "noise": noise,
            "metadata": metadata,
            "error_mitigation": error_mitigation,
        }
        job_data.update({key: value for key, value in optional_fields.items() if value is not None})
        if is_single_input:
            job_data["input"] = run_input
        else:
            all_formats = {run["format"] for run in run_input}
            if len(all_formats) > 1:
                raise ValueError("All runs must have the same format")

            all_gatesets = {run["gateset"] for run in run_input}
            if len(all_gatesets) > 1:
                raise ValueError("All runs must have the same gateset")

            qubits = max(run["qubits"] for run in run_input)
            circuits = [{"circuit": run, "name": f"Circuit {i}"} for i, run in enumerate(run_input)]

            job_data["input"] = {
                "format": all_formats.pop(),
                "gateset": all_gatesets.pop(),
                "qubits": qubits,
                "circuits": circuits,
            }
        serialized_data = json.dumps(job_data)
        job_data = self.session.create_job(serialized_data)
        job_id = job_data.get("id")
        if not job_id:
            raise ValueError("Job ID not found in the response")
        return IonQJob(job_id=job_id, session=self.session, device=self, shots=shots)

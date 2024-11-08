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
from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.programs import load_program
from qbraid.programs.typer import IonQDict, IonQDictType, QasmStringType
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

    @staticmethod
    def _squash_multicircuit_input(batch_input: list[IonQDictType]) -> dict[str, Any]:
        if not batch_input:
            raise ValueError("run_input list cannot be empty.")

        default_format = "ionq.circuit.v0"
        default_gateset = "qis"

        input_format = batch_input[0].get("format", default_format)
        input_gateset = batch_input[0].get("gateset", default_gateset)
        max_qubits = 0
        circuits = []

        for i, run_input in enumerate(batch_input):
            if not isinstance(run_input, IonQDict):
                raise ValueError("All run_inputs must be an instance of ~IonQDict.")
            if run_input.get("format", default_format) != input_format:
                raise ValueError("All run_inputs must have the same value for key 'format'.")
            if run_input.get("gateset", default_gateset) != input_gateset:
                raise ValueError("All run_inputs must have the same value for key 'gateset'.")

            max_qubits = max(max_qubits, run_input["qubits"])
            circuits.append({"circuit": run_input["circuit"], "name": f"Circuit {i}"})

        return {
            "format": input_format,
            "gateset": input_gateset,
            "qubits": max_qubits,
            "circuits": circuits,
        }

    # pylint:disable-next=arguments-differ,too-many-arguments
    def submit(
        self,
        run_input: Union[IonQDictType, list[IonQDictType]],
        shots: int,
        preflight: bool = False,
        name: Optional[str] = None,
        noise: Optional[dict[str, Any]] = None,
        error_mitigation: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> IonQJob:
        """Submit a job to the IonQ device."""
        ionq_input = (
            self._squash_multicircuit_input(run_input) if isinstance(run_input, list) else run_input
        )
        job_data = {
            "target": self.id,
            "shots": shots,
            "preflight": preflight,
            "input": ionq_input,
            **kwargs,
        }
        optional_fields = {
            "name": name,
            "noise": noise,
            "metadata": metadata,
            "error_mitigation": error_mitigation,
        }
        job_data.update({key: value for key, value in optional_fields.items() if value is not None})
        serialized_data = json.dumps(job_data)
        job_data = self.session.create_job(serialized_data)
        job_id = job_data.get("id")
        if not job_id:
            raise ValueError("Job ID not found in the response")
        return IonQJob(job_id=job_id, session=self.session, device=self, shots=shots)

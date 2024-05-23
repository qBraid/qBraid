# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

from qbraid.programs import load_program, QPROGRAM
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus, DeviceType

from qcaas_client.client import OQCClient, QPUTask

from .job import OQCJob

class OQCDevice(QuantumDevice):

    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        client: "qcaas_client.client.OQCClient",
    ):
        super().__init__(profile=profile)
        self._client = client

    @property
    def client(self) -> "qcaas_client.client.OQCClient":
        return self._client
    
    def status(self) -> DeviceStatus:
        if self.profile.get("device_type") == DeviceType.SIMULATOR:
            return DeviceStatus.ONLINE
        else:
            raise NotImplementedError("Only OQC simulators are supported")

    def submit(self, run_input, **kwargs) -> OQCJob:
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        tasks = []
        for program in run_input:
            if not isinstance(program, str):
                error_msg = f"Expected str, got {type(program)}"
                raise TypeError(error_msg)

            task = QPUTask(program=program)
            tasks.append(task)

        qpu_tasks = self._client.schedule_tasks(tasks, qpu_id = self.id)
        job_ids = [task.task_id for task in qpu_tasks]

        return [OQCJob(job_id = id_str, qpu_id = self.id, client=self._client) for id_str in job_ids] if not is_single_input else OQCJob(job_id = job_ids[0], qpu_id = self.id, client=self._client)



    

# Copyright 2023 qBraid
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
Module defining BraketDeviceWrapper Class

"""
from typing import TYPE_CHECKING

from braket.aws import AwsDevice

from qbraid.api.config_user import get_config
from qbraid.api.job_api import init_job
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError

from .job import BraketQuantumTaskWrapper

if TYPE_CHECKING:
    import braket

    import qbraid


class BraketDeviceWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(self, **kwargs):
        """Create a BraketDeviceWrapper."""

        super().__init__(**kwargs)
        bucket = get_config("s3_bucket", "AWS")
        folder = get_config("s3_folder", "AWS")
        self._s3_location = (bucket, folder)
        self._arn = self._obj_arg

    def _get_device(self):
        """Initialize an AWS device."""
        try:
            return AwsDevice(self._obj_arg)
        except ValueError as err:
            raise DeviceError("Device not found") from err

    def _vendor_compat_run_input(self, run_input):
        return run_input

    @property
    def status(self) -> "qbraid.devices.DeviceStatus":
        """Return the status of this Device.

        Returns:
            The status of this Device
        """
        if self.vendor_dlo.status == "OFFLINE":
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

    def run(
        self, run_input: "braket.circuits.Circuit", *args, **kwargs
    ) -> "qbraid.device.aws.BraketQuantumTaskWrapper":
        """Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        run_input, qbraid_circuit = self._compat_run_input(run_input)
        aws_quantum_task = self.vendor_dlo.run(run_input, self._s3_location, *args, **kwargs)
        metadata = aws_quantum_task.metadata()
        shots = 0 if "shots" not in metadata else metadata["shots"]
        vendor_job_id = aws_quantum_task.metadata()["quantumTaskArn"]
        job_id = init_job(vendor_job_id, self, qbraid_circuit, shots)
        return BraketQuantumTaskWrapper(
            job_id, vendor_job_id=vendor_job_id, device=self, vendor_jlo=aws_quantum_task
        )

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
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Union

from braket.aws import AwsDevice
from braket.aws.aws_session import AwsSession
from braket.device_schema import DeviceCapabilities, ExecutionDay
from braket.schema_common import BraketSchemaBase

from qbraid.api.config_user import get_config
from qbraid.api.job_api import init_job
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError

from .job import BraketQuantumTaskWrapper

if TYPE_CHECKING:
    import braket

    import qbraid


class AwsDeviceType(str, Enum):
    """Possible AWS device types"""

    SIMULATOR = "SIMULATOR"
    QPU = "QPU"


class BraketDeviceWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(self, **kwargs):
        """Create a BraketDeviceWrapper."""

        super().__init__(**kwargs)
        bucket = get_config("s3_bucket", "AWS")
        folder = get_config("s3_folder", "AWS")
        self._s3_location = (bucket, folder)
        self._arn = self._obj_arg
        self._aws_session = self._get_device()._aws_session
        self.refresh_metadata()

    def _get_device(self):
        """Initialize an AWS device."""
        try:
            return AwsDevice(self._obj_arg)
        except ValueError as err:
            raise DeviceError("Device not found") from err

    def _vendor_compat_run_input(self, run_input):
        return run_input

    def refresh_metadata(self) -> None:
        """
        Refresh the `AwsDevice` object with the most recent Device metadata.
        """
        self._populate_properties(self._aws_session)

    def _populate_properties(self, session: AwsSession) -> None:
        metadata = session.get_device(self._arn)
        self._name = metadata.get("deviceName")
        self._status = metadata.get("deviceStatus")
        self._type = AwsDeviceType(metadata.get("deviceType"))
        self._provider_name = metadata.get("providerName")
        self._properties = metadata.get("deviceCapabilities")
        self._frames = None
        self._ports = None

    @property
    def status(self) -> "qbraid.devices.DeviceStatus":
        """Return the status of this Device.

        Returns:
            The status of this Device
        """
        if self.vendor_dlo.status == "OFFLINE":
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

    @property
    def properties(self) -> DeviceCapabilities:
        """DeviceCapabilities: Return the device properties
        Please see `braket.device_schema` in amazon-braket-schemas-python_
        .. _amazon-braket-schemas-python: https://github.com/aws/amazon-braket-schemas-python"""
        return BraketSchemaBase.parse_raw_schema(self._properties)

    @property
    def is_available(self) -> Union[str, bool]:
        """Returns true if the device is currently available, and the available time.
        Returns:
            str: Return device available time.
            bool: Return if the device is currently available.
        """
        if self.status != DeviceStatus.ONLINE:
            return False

        is_available_result = False
        day = 0

        current_datetime_utc = datetime.utcnow()
        for execution_window in self.properties.service.executionWindows:
            weekday = current_datetime_utc.weekday()
            current_time_utc = current_datetime_utc.time().replace(microsecond=0)

            if (
                execution_window.windowEndHour < execution_window.windowStartHour
                and current_time_utc < execution_window.windowEndHour
            ):
                weekday = (weekday - 1) % 7

            matched_day = execution_window.executionDay == ExecutionDay.EVERYDAY
            matched_day = matched_day or (
                execution_window.executionDay == ExecutionDay.WEEKDAYS and weekday < 5
            )
            matched_day = matched_day or (
                execution_window.executionDay == ExecutionDay.WEEKENDS and weekday > 4
            )
            ordered_days = (
                ExecutionDay.MONDAY,
                ExecutionDay.TUESDAY,
                ExecutionDay.WEDNESDAY,
                ExecutionDay.THURSDAY,
                ExecutionDay.FRIDAY,
                ExecutionDay.SATURDAY,
                ExecutionDay.SUNDAY,
            )
            matched_day = matched_day or (
                execution_window.executionDay in ordered_days
                and ordered_days.index(execution_window.executionDay) == weekday
            )

            matched_time = (
                execution_window.windowStartHour < execution_window.windowEndHour
                and execution_window.windowStartHour
                <= current_time_utc
                <= execution_window.windowEndHour
            ) or (
                execution_window.windowEndHour < execution_window.windowStartHour
                and (
                    current_time_utc >= execution_window.windowStartHour
                    or current_time_utc <= execution_window.windowEndHour
                )
            )

            def time_subtract(start_time, end_time):
                td = timedelta(
                    hours=start_time.hour, minutes=start_time.minute, seconds=start_time.second
                ) - timedelta(hours=end_time.hour, minutes=end_time.minute, seconds=end_time.second)
                hours = td.seconds // 3600
                minutes = (td.seconds // 60) % 60
                seconds = td.seconds - hours * 3600 - minutes * 60
                return f"{day}days {hours}hours {minutes}minutes {seconds}seconds"

            if execution_window.executionDay in ordered_days:
                day = (ordered_days.index(execution_window.executionDay) - weekday) % 6
            if matched_time:
                available_time = time_subtract(execution_window.windowEndHour, current_time_utc)
            else:
                available_time = time_subtract(execution_window.windowStartHour, current_time_utc)

            is_available_result = is_available_result or (matched_day and matched_time)

            avaliable = (
                f"Available time remain:{available_time}"
                if is_available_result
                else f"Next available in:{available_time}"
            )

        return is_available_result, avaliable

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

# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining BraketDeviceWrapper Class

"""
import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from braket.device_schema import ExecutionDay

from qbraid.programs._import import QPROGRAM_LIBS
from qbraid.programs.libs.braket import BraketCircuit
from qbraid.providers.device import QuantumDevice
from qbraid.providers.enums import DeviceStatus, DeviceType

from .job import BraketQuantumTask

if TYPE_CHECKING:
    import braket.aws
    import braket.circuits

    import qbraid.providers.aws
    import qbraid.transpiler


def _future_utc_datetime(hours: int, minutes: int, seconds: int) -> str:
    """Return a UTC datetime that is hours, minutes, and seconds from now
    as an ISO string without fractional seconds."""
    current_utc = datetime.utcnow()
    future_time = current_utc + timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return future_time.strftime("%Y-%m-%dT%H:%M:%SZ")


class BraketDevice(QuantumDevice):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(self, aws_device: "braket.aws.AwsDevice"):
        """Create a BraketDevice."""

        super().__init__(aws_device)
        self._vendor = "AWS"
        self._run_package = "braket"

    def _populate_metadata(self, device: "braket.aws.AwsDevice") -> None:
        """Populate device metadata using BraketSchemaBase"""
        # pylint: disable=attribute-defined-outside-init
        metadata = device.aws_session.get_device(device.arn)
        capabilities = json.loads(metadata.get("deviceCapabilities"))

        self._vendor_id = metadata.get("deviceArn")
        self._name = metadata.get("deviceName")
        self._provider = metadata.get("providerName")
        self._device_type = DeviceType(metadata.get("deviceType"))

        try:
            self._num_qubits = capabilities["paradigm"]["qubitCount"]
        except KeyError:
            self._num_qubits = None

    def status(self) -> "qbraid.providers.DeviceStatus":
        """Return the status of this Device.

        Returns:
            The status of this Device
        """
        if self._device.is_available:
            return DeviceStatus.ONLINE

        if self._device.status == "RETIRED":
            return DeviceStatus.RETIRED

        return DeviceStatus.OFFLINE

    def availability_window(self) -> Tuple[bool, str, str]:
        """Provides device availability status. Indicates current availability,
        time remaining (hours, minutes, seconds) until next availability or
        unavailability, and future UTC datetime of next change in availability status.

        Returns:
            Tuple[bool, str, str]: Current device availability, hr/min/sec until availability
                                   switch, future UTC datetime of availability switch
        """

        is_available_result = False
        available_time = None

        device = self._device

        if device.status != "ONLINE":
            return is_available_result, "", ""

        day = 0

        current_datetime_utc = datetime.utcnow()
        for execution_window in device.properties.service.executionWindows:
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

            if execution_window.executionDay in ordered_days:
                day = (ordered_days.index(execution_window.executionDay) - weekday) % 6

            start_time = execution_window.windowStartHour
            end_time = current_time_utc

            if day == 0:
                day_factor = day
            elif start_time.hour < end_time.hour:
                day_factor = day - 1
            elif start_time.hour == end_time.hour:
                if start_time.minute < end_time.minute:
                    day_factor = day - 1
                elif start_time.minute == end_time.minute:
                    if start_time.second <= end_time.second:
                        day_factor = day - 1
            else:
                day_factor = day

            td = timedelta(
                hours=start_time.hour,
                minutes=start_time.minute,
                seconds=start_time.second,
            ) - timedelta(hours=end_time.hour, minutes=end_time.minute, seconds=end_time.second)
            days_seconds = 86400 * day_factor
            available_time_secs = td.seconds + days_seconds

            if available_time is None or available_time_secs < available_time:
                available_time = available_time_secs

            is_available_result = is_available_result or (matched_day and matched_time)

        if available_time is None:
            return is_available_result, "", ""

        hours = available_time // 3600
        minutes = (available_time // 60) % 60
        seconds = available_time - hours * 3600 - minutes * 60
        available_time_hms = f"{hours:02}:{minutes:02}:{seconds:02}"
        utc_datetime_str = _future_utc_datetime(hours, minutes, seconds)
        return is_available_result, available_time_hms, utc_datetime_str

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the device."""
        queue_depth_info = self._device.queue_depth()
        total_queued = 0
        for queue_type in ["Normal", "Priority"]:
            num_queued = queue_depth_info.quantum_tasks[queue_type]
            if isinstance(num_queued, str) and num_queued.startswith(">"):
                num_queued = num_queued[1:]
            total_queued += int(num_queued)
        return total_queued

    def _transpile(self, run_input):
        """Transpile a circuit for the device."""
        if self._device_type.name == "SIMULATOR":
            program = BraketCircuit(run_input)
            program.remove_idle_qubits()
            run_input = program.program

        return run_input

    def _compile(self, run_input):
        """Compile a circuit for the device."""
        if self.provider.lower() == "ionq" and "pytket" in QPROGRAM_LIBS:
            # pylint: disable=import-outside-toplevel
            from qbraid.compiler.braket.ionq import braket_ionq_compile

            run_input = braket_ionq_compile(run_input)
        return run_input

    def _run(self, run_input: "braket.circuits.Circuit", *args, **kwargs) -> Dict[str, Any]:
        """Run a quantum task specification on this quantum device. Task must represent a
        quantum circuit, annealing problems not supported.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        aws_quantum_task = self._device.run(run_input, *args, **kwargs)
        metadata = aws_quantum_task.metadata()
        return {
            "vendor_job_id": metadata["quantumTaskArn"],
            "tags": metadata.get("tags", {}),
            "shots": metadata.get("shots", 0),
            "vendor_job_obj": aws_quantum_task,
            "qbraid_job_obj": BraketQuantumTask,
        }

    def _run_batch(self, run_input, *args, **kwargs) -> List[Dict[str, Any]]:
        """Run batch of quantum tasks on this quantum device.

        Args:
            run_input: A circuit object list to run on the wrapped device.

        Keyword Args:
            auto_compile (bool): Whether to compile the circuits for the device before running.
            shots (int): The number of times to run the task on the device. Default is 1024.

        Returns:
            List of BraketQuantumTask objects for the run.

        """
        device = self._device
        aws_quantum_task_batch = device.run_batch(run_input, *args, **kwargs)
        aws_quantum_tasks = aws_quantum_task_batch.tasks
        aws_quantum_task_data = []
        for _, aws_quantum_task in enumerate(aws_quantum_tasks):
            metadata = aws_quantum_task.metadata()
            job_data = {
                "vendor_job_id": metadata["quantumTaskArn"],
                "tags": metadata.get("tags", {}),
                "shots": metadata.get("shots", 0),
                "vendor_job_obj": aws_quantum_task,
                "qbraid_job_obj": BraketQuantumTask,
            }
            aws_quantum_task_data.append(job_data)
        return aws_quantum_task_data

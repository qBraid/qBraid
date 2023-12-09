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
from typing import TYPE_CHECKING, List, Tuple

from braket.device_schema import ExecutionDay

from qbraid._qprogram import QPROGRAM_LIBS
from qbraid.providers.device import QuantumDevice
from qbraid.providers.enums import DeviceStatus, DeviceType

from .job import BraketQuantumTask

if TYPE_CHECKING:
    import braket.aws

    import qbraid


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

        self._id = metadata.get("deviceArn")
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

    @property
    def is_available(self) -> Tuple[bool, str]:
        """Returns true if the device is currently available, and the available time.

        Returns:
            Tuple[bool, str]: Current device availability and hr/min/sec until next available.
        """

        is_available_result = False
        available_time = None

        device = self._device

        if device.status != "ONLINE":
            return is_available_result, ""

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
            return is_available_result, ""

        hours = available_time // 3600
        minutes = (available_time // 60) % 60
        seconds = available_time - hours * 3600 - minutes * 60
        time_lst = [hours, minutes, seconds]
        time_str_lst = [str(x) if x >= 10 else f"0{x}" for x in time_lst]
        available_time_hms = ":".join(time_str_lst)
        return is_available_result, available_time_hms

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the device"""
        aws_device = self._device
        queue_depth_info = aws_device.queue_depth()
        queued_tasks = queue_depth_info.quantum_tasks
        num_queued_normal = queued_tasks["Normal"]
        num_queued_priority = queued_tasks["Priority"]
        return int(num_queued_normal) + int(num_queued_priority)

    def _transpile(self, run_input):
        """Transpile a circuit for the device."""
        return run_input

    def _compile(self, run_input):
        """Compile a circuit for the device."""
        if self.provider.lower() == "ionq" and "pytket" in QPROGRAM_LIBS:
            # pylint: disable=import-outside-toplevel
            from qbraid.compiler.braket.ionq import braket_ionq_compile

            run_input = braket_ionq_compile(run_input)
        return run_input

    def run(
        self, run_input, *args, auto_compile: bool = False, **kwargs
    ) -> "qbraid.device.aws.BraketQuantumTaskWrapper":
        """Run a quantum task specification on this quantum device. Task must represent a
        quantum circuit, annealing problems not supported.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            auto_compile (bool): Whether to compile the circuit for the device before running.
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        qbraid_circuit = self.process_run_input(run_input, auto_compile=auto_compile)
        run_input = qbraid_circuit._program
        aws_quantum_task = self._device.run(run_input, *args, **kwargs)
        metadata = aws_quantum_task.metadata()
        shots = 0 if "shots" not in metadata else metadata["shots"]
        vendor_job_id = metadata["quantumTaskArn"]
        job_id = self._init_job(vendor_job_id, [qbraid_circuit], shots)
        return BraketQuantumTask(
            job_id, vendor_job_id=vendor_job_id, device=self, vendor_job_obj=aws_quantum_task
        )

    def run_batch(
        self, run_input, *args, auto_compile: bool = False, **kwargs
    ) -> List["qbraid.device.aws.BraketQuantumTaskWrapper"]:
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
        qbraid_circuit_batch = []
        run_input_batch = []
        for circuit in run_input:
            qbraid_circuit = self.process_run_input(circuit, auto_compile=auto_compile)
            run_input = qbraid_circuit._program
            run_input_batch.append(run_input)
            qbraid_circuit_batch.append(qbraid_circuit)
        aws_quantum_task_batch = device.run_batch(run_input_batch, *args, **kwargs)
        aws_quantum_tasks = aws_quantum_task_batch.tasks
        aws_quantum_task_wrapper_list = []
        for index, aws_quantum_task in enumerate(aws_quantum_tasks):
            qbraid_circuit = qbraid_circuit_batch[index]
            metadata = aws_quantum_task.metadata()
            shots = 0 if "shots" not in metadata else metadata["shots"]
            vendor_job_id = metadata["quantumTaskArn"]
            job_id = self._init_job(vendor_job_id, [qbraid_circuit], shots)
            aws_quantum_task_wrapper_list.append(
                BraketQuantumTask(
                    job_id,
                    vendor_job_id=vendor_job_id,
                    device=self,
                    vendor_job_obj=aws_quantum_task,
                )
            )
        return aws_quantum_task_wrapper_list

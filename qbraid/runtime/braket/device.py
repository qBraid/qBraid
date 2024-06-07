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
Module defining BraketDeviceWrapper Class

"""
from typing import TYPE_CHECKING, Optional, Union

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.aws import AwsDevice
from braket.circuits import Circuit

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.transforms.braket import transform

from .availability import next_available_time
from .job import BraketQuantumTask

if TYPE_CHECKING:
    import braket.aws

    import qbraid.runtime
    import qbraid.runtime.braket
    import qbraid.transpiler


class BraketDevice(QuantumDevice):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        session: "Optional[braket.aws.AwsSession]" = None,
    ):
        """Create a BraketDevice."""
        super().__init__(profile=profile)
        self._device = AwsDevice(arn=self.id, aws_session=session)
        self._provider_name = self.profile.get("provider_name")

    @property
    def name(self) -> str:
        """Return the name of this Device."""
        return self._device.name

    def __str__(self):
        """Official string representation of QuantumDevice object."""
        return f"{self.__class__.__name__}('{self._provider_name} {self.name}')"

    def status(self) -> "qbraid.runtime.DeviceStatus":
        """Return the status of this Device."""
        if self._device.status == "ONLINE":
            if self._device.is_available:
                return DeviceStatus.ONLINE
            return DeviceStatus.UNAVAILABLE

        if self._device.status == "RETIRED":
            return DeviceStatus.RETIRED

        return DeviceStatus.OFFLINE

    def availability_window(self) -> tuple[bool, str, str]:
        """Provides device availability status. Indicates current availability,
        time remaining (hours, minutes, seconds) until next availability or
        unavailability, and future UTC datetime of next change in availability status.

        Returns:
            tuple[bool, str, Optional[str]]: Current device availability, hr/min/sec until
                availability switch, future UTC datetime of availability switch
        """
        return next_available_time(self._device)

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

    def transform(
        self, run_input: Union[Circuit, AnalogHamiltonianSimulation]
    ) -> Union[Circuit, AnalogHamiltonianSimulation]:
        """Transpile a circuit for the device."""
        return transform(run_input, device=self)

    def submit(
        self,
        run_input: Union[
            Circuit, AnalogHamiltonianSimulation, list[Circuit], list[AnalogHamiltonianSimulation]
        ],
        *args,
        **kwargs,
    ) -> Union[BraketQuantumTask, list[BraketQuantumTask]]:
        """Run a quantum task specification on this quantum device. Task must represent a
        quantum circuit, annealing problems not supported.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        aws_quantum_task_batch = self._device.run_batch(run_input, *args, **kwargs)
        tasks = [
            BraketQuantumTask(task.id, task=task, device=self._device)
            for task in aws_quantum_task_batch.tasks
        ]
        if is_single_input:
            return tasks[0]
        return tasks

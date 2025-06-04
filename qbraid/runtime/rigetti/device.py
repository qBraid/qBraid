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
Module defining Rigettu device class

"""

import pyquil
import pyquil.api

from qbraid.runtime import QuantumDevice, TargetProfile
from qbraid.runtime.enums import DeviceStatus

from .job import RigettiJob


class RigettiDevice(QuantumDevice):
    """
    Wraps a single Rigetti QCS quantum processor or simulator.
    """

    def __init__(
        self,
        profile: TargetProfile,
        qc: pyquil.api.QuantumComputer,
    ):
        """
        profile: A TargetProfile object (constructed by RigettiProvider).
        """
        # Call base class initializer, passing the TargetProfile
        super().__init__(profile=profile)
        self._qc = qc

    def status(self) -> DeviceStatus:
        """
        Return the current status of the device.
        This is a placeholder; actual implementation may vary based on QCS API.
        """
        # For now, we assume the device is always available
        if self._qc.qubits():
            return DeviceStatus.ONLINE
        return DeviceStatus.OFFLINE

    def submit(self, run_input: pyquil.Program, *args, **kwargs):
        compiled_program = self._qc.compile(run_input)
        execute_response = self._qc.qam.execute(compiled_program, *args, **kwargs)
        if isinstance(execute_response, pyquil.api.QPUExecuteResponse):
            job_id = execute_response.job_id
        else:
            job_id = "simulator-job"
        return RigettiJob(
            job_id=job_id,
            qam=self._qc.qam,
            execute_response=execute_response,
            device_id=self.id,
        )

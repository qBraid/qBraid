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

from multiprocessing.pool import ThreadPool
from typing import Union

import pyquil.api
from pyquil.api import get_qc
from qcs_sdk.qpu.api import SubmissionError
from qcs_sdk.qpu.isa import GetISAError, get_instruction_set_architecture

from qbraid.runtime import QuantumDevice, TargetProfile
from qbraid.runtime.enums import DeviceStatus

from .job import RigettiJob, RigettiJobError


class RigettiDevice(QuantumDevice):
    """
    Wraps a single Rigetti QCS quantum processor or simulator.
    """

    def __init__(
        self,
        profile: TargetProfile,
        qcs_client: pyquil.api.QCSClient,
    ):
        """
        profile: A TargetProfile object (constructed by RigettiProvider).
        """
        # Call base class initializer, passing the TargetProfile
        super().__init__(profile=profile)
        self._qcs_client = qcs_client
        self._qc = get_qc(
            name=profile.device_id, as_qvm=profile.simulator, client_configuration=qcs_client
        )

    def status(self) -> DeviceStatus:
        """
        Return the current status of the device.
        This is a placeholder; actual implementation may vary based on QCS API.
        """
        # For now, we assume the device is always available
        if self.profile.simulator:
            # If it's a simulator, we consider it always online
            return DeviceStatus.ONLINE
        try:
            get_instruction_set_architecture(
                quantum_processor_id=self.profile.device_id,
                client=self._qcs_client,
            )
        except GetISAError:
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

    def _submit(self, run_input: pyquil.Program, *args, **kwargs) -> RigettiJob:
        """
        Submit a job to the Rigetti device.
        """
        compiled_program = self._qc.compile(run_input)
        try:
            execute_response = self._qc.qam.execute(compiled_program, *args, **kwargs)
        except SubmissionError as e:
            raise RigettiJobError("Failed to submit job to Rigetti QCS.") from e
        if isinstance(execute_response, pyquil.api.QPUExecuteResponse):
            job_id = execute_response.job_id
        else:
            job_id = "simulator-job"
        return RigettiJob(
            job_id=job_id,
            qam=self._qc.qam,
            execute_response=execute_response,
            device=self,
        )

    def submit(
        self, run_input: Union[pyquil.Program, list[pyquil.Program]], *args, **kwargs
    ) -> Union[RigettiJob, list[RigettiJob]]:
        """
        Submit one or more jobs to the Rigetti device.
        """
        if isinstance(run_input, list):
            quantum_jobs = []
            with ThreadPool(5) as pool:
                quantum_jobs = pool.map(
                    lambda job: self._submit(job, *args, **kwargs), quantum_jobs
                )
            return quantum_jobs

        return self._submit(run_input, *args, **kwargs)

    def live_qubits(self) -> list[int]:
        """
        Returns a list of live qubits for the device.
        """
        return [q.id for q in self._qc.to_compiler_isa().qubits.values() if not q.dead]

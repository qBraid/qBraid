# Copyright 2026 qBraid
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
Module defining Rigetti device class
"""

from multiprocessing.pool import ThreadPool
from typing import Union

import pyquil
from qcs_sdk.client import QCSClient
from qcs_sdk.qpu.api import SubmissionError
from qcs_sdk.qpu.api import submit as qpu_submit
from qcs_sdk.qpu.isa import GetISAError, get_instruction_set_architecture
from qcs_sdk.qpu.translation import translate

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
        qcs_client: QCSClient,
    ):
        """
        profile: A TargetProfile object (constructed by RigettiProvider).
        """
        # Call base class initializer, passing the TargetProfile
        super().__init__(profile=profile)
        self._qcs_client = qcs_client

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

    def _submit(self, run_input: pyquil.Program, *_args, **_kwargs) -> RigettiJob:
        """
        Submit a native Quil program to the Rigetti QPU.

        Uses qcs_sdk translate + submit directly with our authenticated client.
        The program must already be in native gates (RZ, RX, CZ, MEASURE).
        """
        quil_program = run_input.out()
        num_shots = run_input.num_shots or 1
        quantum_processor_id = self.profile.device_id

        # TODO: figure out how to add the quilc compilation step here
        #       Either we need to host that compiler or there must be
        #       some way for us to use it in the local system
        translation_result = translate(
            native_quil=quil_program,
            num_shots=num_shots,
            quantum_processor_id=quantum_processor_id,
            client=self._qcs_client,
        )

        try:
            job_id = qpu_submit(
                program=translation_result.program,
                patch_values={},
                quantum_processor_id=quantum_processor_id,
                client=self._qcs_client,
            )
        except SubmissionError as e:
            raise RigettiJobError("Failed to submit job to Rigetti QCS.") from e

        return RigettiJob(
            job_id=job_id,
            device=self,
            num_shots=num_shots,
        )

    def submit(
        self, run_input: Union[pyquil.Program, list[pyquil.Program]], *args, **kwargs
    ) -> Union[RigettiJob, list[RigettiJob]]:
        """
        Submit one or more jobs to the Rigetti device.
        """
        if isinstance(run_input, list):
            with ThreadPool(5) as pool:
                quantum_jobs = pool.map(lambda job: self._submit(job, *args, **kwargs), run_input)
                return quantum_jobs

        return self._submit(run_input, *args, **kwargs)

    def live_qubits(self) -> list[int]:
        """
        Returns a list of live qubit IDs for the device.
        """
        isa = get_instruction_set_architecture(
            quantum_processor_id=self.profile.device_id,
            client=self._qcs_client,
        )
        return [node.node_id for node in isa.architecture.nodes]

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

# pylint: disable=no-name-in-module

# The above disable is necessary because the qcs_sdk.* modules load from Rust extension bindings
# (__file__ is None for submodules), so pylint/astroid can’t reliably introspect exported names
# and emits E0611 false positives.
"""
Module defining Rigetti device class
"""

from multiprocessing.pool import ThreadPool
from typing import Optional, Union

import pyquil
from qcs_sdk.client import QCSClient
from qcs_sdk.compiler.quilc import QuilcClient, TargetDevice, compile_program
from qcs_sdk.qpu import ListQuantumProcessorsError, list_quantum_processors
from qcs_sdk.qpu.api import ExecutionOptions, SubmissionError
from qcs_sdk.qpu.api import submit as qpu_submit
from qcs_sdk.qpu.isa import GetISAError, get_instruction_set_architecture
from qcs_sdk.qpu.translation import translate

from qbraid.runtime import QuantumDevice, TargetProfile
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError

from .job import RigettiJob, RigettiJobError


class RigettiDeviceError(QbraidRuntimeError):
    """Class for errors raised while processing a Rigetti device."""


class RigettiDevice(QuantumDevice):
    """
    Wraps a single Rigetti QCS quantum processor or simulator.
    """

    def __init__(
        self,
        profile: TargetProfile,
        qcs_client: QCSClient,
        execution_options: ExecutionOptions | None = None,
    ):
        """
        profile: A TargetProfile object (constructed by RigettiProvider).
        execution_options: ExecutionOptions built by RigettiProvider. If None,
            the SDK default (Gateway strategy) is used.
        """
        super().__init__(profile=profile)
        self._qcs_client = qcs_client
        self._execution_options = execution_options

    def status(self) -> DeviceStatus:
        """
        Return the current status of the device.
        """
        try:
            # Otherwise, check if the quantum processor ID is in the list of available processors
            quantum_processor_ids = set(
                list_quantum_processors(client=self._qcs_client)
            )
            if self.id not in quantum_processor_ids:
                return DeviceStatus.OFFLINE
        except ListQuantumProcessorsError as e:
            raise RigettiDeviceError(
                "Failed to retrieve quantum processor list from Rigetti QCS."
            ) from e
        return DeviceStatus.ONLINE

    def transform(self, run_input):
        """Compile a Quil program into the QPU's native gate set via quilc.

        Accepts either a ``pyquil.Program`` object or a serialized Quil
        string. Returns the same type as the input: ``Program`` in,
        ``Program`` out; ``str`` in, ``str`` out.

        Raises:
            RigettiDeviceError: If quilc compilation fails.
        """
        is_program = isinstance(run_input, pyquil.Program)
        quil_str = run_input.out() if is_program else run_input

        try:
            compilation_result = compile_program(
                quil=quil_str,
                target=TargetDevice.from_isa(
                    get_instruction_set_architecture(
                        quantum_processor_id=self.id, client=self._qcs_client
                    )
                ),
                client=QuilcClient.new_rpcq(self._qcs_client.quilc_url),
            )
            compiled_quil = compilation_result.program.to_quil()
        except Exception as e:
            raise RigettiDeviceError(
                f"Compilation failed for quantum processor '{self.id}'. "
                "Ensure the program is valid Quil and that the quilc "
                "compiler is running and accessible"
            ) from e

        if is_program:
            return pyquil.Program(compiled_quil)
        return compiled_quil

    def _submit(self, run_input: str, shots: Optional[int] = None) -> RigettiJob:
        """
        Submit a Quil program to the Rigetti QPU.

        Args:
            run_input: A serialized Quil program string (produced by prepare()).
            shots: Number of shots for the job.
        """
        num_shots = shots
        if num_shots is None or num_shots <= 0:
            raise RigettiJobError(
                f"Shots > 0 must be specified for Rigetti QPU jobs, current value: {num_shots}."
            )

        compiled_quil = self.transform(run_input)
        if isinstance(compiled_quil, pyquil.Program):
            compiled_quil = compiled_quil.out()

        try:
            translation_result = translate(
                native_quil=compiled_quil,
                num_shots=num_shots,
                quantum_processor_id=self.id,
                client=self._qcs_client,
            )
        except Exception as e:
            raise RigettiJobError(
                f"Translation failed for quantum processor '{self.id}'. "
                "Ensure the program uses only native gates for the target QPU."
            ) from e

        try:
            job_id = qpu_submit(
                program=translation_result.program,
                patch_values={},
                quantum_processor_id=self.id,
                client=self._qcs_client,
                execution_options=self._execution_options,
            )
        except SubmissionError as e:
            raise RigettiJobError("Failed to submit job to Rigetti QCS.") from e

        return RigettiJob(
            job_id=job_id,
            device=self,
            num_shots=num_shots,
            ro_sources=translation_result.ro_sources,
        )

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input: Union[str, list[str]],
        shots: Optional[int] = None,
    ) -> Union[RigettiJob, list[RigettiJob]]:
        """
        Submit one or more jobs to the Rigetti device.
        """
        if isinstance(run_input, list):
            with ThreadPool(5) as pool:
                quantum_jobs = pool.map(lambda job: self._submit(job, shots), run_input)
                return quantum_jobs

        return self._submit(run_input, shots)

    def live_qubits(self) -> list[int]:
        """
        Returns a list of live qubit IDs for the device.
        """
        try:
            isa = get_instruction_set_architecture(
                quantum_processor_id=self.id,
                client=self._qcs_client,
            )
            return [node.node_id for node in isa.architecture.nodes]
        except GetISAError as e:
            raise RigettiDeviceError(
                f"Failed to retrieve ISA for quantum processor '{self.id}'."
            ) from e

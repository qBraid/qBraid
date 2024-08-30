# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=arguments-differ

"""
Module defining QbraidDevice class

"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Optional, Union

from qbraid_core.services.quantum import QuantumClient

from qbraid.programs import ProgramSpec, get_program_type_alias, load_program
from qbraid.programs.qasm_typer import Qasm2Instance, Qasm2String
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus, NoiseModel
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.transpiler import ConversionGraph, transpile

from .job import QbraidJob

if TYPE_CHECKING:
    import pyqir
    import qbraid_core.services.quantum

    import qbraid.programs
    import qbraid.runtime
    import qbraid.transpiler

logger = logging.getLogger(__name__)


class QbraidDevice(QuantumDevice):
    """Class to represent a qBraid device."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        client: Optional[qbraid_core.services.quantum.QuantumClient] = None,
        **kwargs,
    ):
        """Create a new QbraidDevice object."""
        super().__init__(profile=profile, **kwargs)
        self._client = client or QuantumClient()

    @property
    def client(self) -> QuantumClient:
        """Return the QuantumClient object."""
        return self._client

    def status(self) -> qbraid.runtime.DeviceStatus:
        """Return device status."""
        device_data = self.client.get_device(self.id)
        status = device_data.get("status")
        if not status:
            raise QbraidRuntimeError("Failed to retrieve device status")
        return DeviceStatus(status.lower())

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""
        device_data = self.client.get_device(self.id)
        pending_jobs = device_data.get("pendingJobs", 0)
        return int(pending_jobs)

    def transform(
        self, run_input: Union[pyqir.Module, Qasm2String]
    ) -> dict[str, Union[Qasm2String, bytes]]:
        """Transform the input to the format expected by the qBraid API."""
        if isinstance(run_input, Qasm2Instance):
            return {"openQasm": run_input}
        return {"bitcode": run_input.bitcode}

    def submit(  # pylint: disable=too-many-arguments
        self,
        run_input: dict[str, Union[bytes, str]],
        shots: Optional[int] = None,
        tags: Optional[dict[str, str]] = None,
        entrypoint: Optional[str] = None,
        noise_model: Optional[str] = None,
        seed: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> qbraid.runtime.QbraidJob:
        """
        Creates a qBraid Quantum Job.

        Args:
            run_input (dict[str, Union[bytes, str]]): Dictionary containing
                QIR bytecode or OpenQASM string to be run on the device.
            shots (optional, int): The number of times to repeat the execution of the
                program. Default value varies by device.
            tags (optional, dict): A dictionary of tags to associate with the job.
            entrypoint (optional, str): Name of the entrypoint function to execute.
                Only applicable if run_input is a QIR module. Defaults to None.
            noise_model (optional, str): The noise model to apply to the job.
                Only applicable if device supports noisey simulation. Defaults to None.
            seed (optional, int): The seed to use for the random number generator.
                Only applicable for certain devices. Defaults to None.
            timeout (optional, int): The maximum time in seconds to wait for the job
                to complete after execution has started. Defaults to None.

        Returns:
            QbraidJob: The job objects representing the submitted job.

        See Also: https://docs.qbraid.com/api-reference/api-reference/post-quantum-jobs

        """
        payload = {
            "qbraidDeviceId": self.id,
            "tags": json.dumps(tags or {}),
            "shots": shots,
            "seed": seed,
            "entrypoint": entrypoint,
            "timeout": timeout,
            "noiseModel": noise_model,
            **run_input,
        }

        job_data = self.client.create_job(data=payload)
        job_id: str = job_data.pop("qbraidJobId")
        job_data["job_id"] = job_id

        return QbraidJob(**job_data, device=self, client=self.client)

    def try_extracting_info(self, func, error_message):
        """Try to extract information from a function/attribute,
        logging an error if it fails."""
        try:
            return func()
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.info("%s: %s. Field will be omitted in job metadata.", error_message, str(err))
            return None

    def _extract_qasm_rep(
        self, program: qbraid.programs.QPROGRAM, program_spec: ProgramSpec
    ) -> Optional[str]:
        """Populate the qasm info in the payload."""
        if program_spec.alias in ["qasm2", "qasm3"]:
            return program

        aux_graph = ConversionGraph()

        closest_qasm = aux_graph.closest_target(program_spec.alias, ["qasm2", "qasm3"])

        if closest_qasm is None:
            return None

        return transpile(program, closest_qasm, conversion_graph=aux_graph)

    def run(
        self,
        run_input: Union[qbraid.programs.QPROGRAM, list[qbraid.programs.QPROGRAM]],
        shots: Optional[int] = None,
        tags: Optional[dict[str, str]] = None,
        **kwargs,
    ) -> Union[qbraid.runtime.QbraidJob, list[qbraid.runtime.QbraidJob]]:
        """
        Run a quantum job or a list of quantum jobs on this quantum device.

        Args:
            run_input (Union[QPROGRAM, list[QPROGRAM]]): A single quantum program
                or a list of quantum programs to run on the device.
            shots (optional, int): The number of times to repeat the execution of the
                program. Default value varies by device.
            tags (optional, dict): A dictionary of tags to associate with the job.
            **kwargs: Additional json data to include in the job submission payload.

        Returns:
            A QuantumJob object or a list of QuantumJob objects corresponding to the input.

        Raises:
            ValueError: If any protected dynamic parameters are specified in the kwargs.
        """
        dynamic_params = {
            "openQasm": None,
            "bitcode": None,
            "circuitNumQubits": None,
            "circuitDepth": None,
        }
        forbidden_keys = set(dynamic_params.keys())

        if any(key in kwargs for key in forbidden_keys):
            raise ValueError(
                f"You cannot specify {', '.join(forbidden_keys)} "
                "as they are dynamically determined."
            )

        if not isinstance(run_input, list):
            run_input_list = [run_input]
            is_single_input = True
        else:
            run_input_list = run_input
            is_single_input = False

        noise_model: Optional[NoiseModel] = kwargs.pop("noise_model", None)
        if noise_model:
            if noise_model not in self.profile.get("noise_models", []):
                raise ValueError(f"Noise model '{noise_model}' not supported by device.")
            noise_model = noise_model.value
            kwargs["noise_model"] = noise_model

        jobs: list[qbraid.runtime.QbraidJob] = []

        for program in run_input_list:
            program_alias = get_program_type_alias(program, safe=True)
            program_spec = ProgramSpec(type(program), alias=program_alias)
            qbraid_program = load_program(program) if program_spec.native else None
            aux_payload = {}

            if qbraid_program:
                aux_payload["circuitNumQubits"] = self.try_extracting_info(
                    lambda program=qbraid_program: program.num_qubits,
                    "Error calculating circuit number of qubits.",
                )
                aux_payload["circuitDepth"] = self.try_extracting_info(
                    lambda program=qbraid_program: program.depth, "Error calculating circuit depth."
                )

            aux_payload["openQasm"] = self.try_extracting_info(
                lambda program=program, program_spec=program_spec: self._extract_qasm_rep(
                    program, program_spec
                ),
                "Error extracting OpenQASM string representation.",
            )

            self.validate(qbraid_program)
            transpiled_program = self.transpile(program, program_spec)
            run_input_json = self.transform(transpiled_program)
            runtime_payload = {**aux_payload, **run_input_json}
            job = self.submit(run_input=runtime_payload, shots=shots, tags=tags, **kwargs)
            jobs.append(job)

        return jobs[0] if is_single_input else jobs

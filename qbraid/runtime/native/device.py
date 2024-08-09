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
Module defining QbraidDevice class

"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid_core.services.quantum import QuantumClient

from qbraid.programs import ProgramSpec, get_program_type_alias, load_program
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.transpiler import transpile

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

    # pylint: disable-next=too-many-arguments
    def _create_job(
        self,
        tags: Optional[dict[str, str]] = None,
        shots: Optional[int] = None,
        openqasm: Optional[str] = None,
        bitcode: Optional[bytes] = None,
        num_qubits: Optional[int] = None,
        depth: Optional[int] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create new qBraid job.

        Args:
            tags (optional, dict): A dictionary of tags to associate with the job.
            shots (optional, int): The number of shots to run the job for.
            bitcode (optional, bytes): The QIR byte code to run.
            openqasm (optional, str): The OpenQASM to run.
            num_qubits (optional, int): The number of qubits in the circuit.
            depth (optional, int): The depth of the circuit.

        Returns:
            dict: The job data returned by the qBraid API.

        """
        tags = tags or {}

        init_data = {
            "bitcode": bitcode,
            "qbraidDeviceId": self.id,
            "shots": shots,
            "openQasm": openqasm,
            "circuitNumQubits": num_qubits,
            "circuitDepth": depth,
            "tags": json.dumps(tags),
            **kwargs,
        }

        job_data = self.client.create_job(data=init_data)
        job_id: str = job_data.pop("qbraidJobId")
        job_data["job_id"] = job_id

        return job_data

    def submit(
        self,
        run_input: pyqir.Module,
        *args,
        entrypoint: Optional[str] = None,
        shots: Optional[int] = None,
        **kwargs,
    ) -> qbraid.runtime.QbraidJob:
        """Runs the qir-runner executable with the given QIR file and shots, each module
        paired with a specific entrypoint.

        Args:
            run_input (pyqir.Module): QIR modules to run in the simulator.
            entrypoint (optional, str): Name of the entrypoint function to execute in
                the QIR program. Defaults to None if not specified.
            shots (optional, int): The number of times to repeat the execution of the chosen
                entry point in the program. Defaults to 1 if not specified.

        Returns:
            QbraidJob: The job objects representing the submitted job.
        """
        job_data = self._create_job(
            bitcode=run_input.bitcode, entrypoint=entrypoint, shots=shots, **kwargs
        )
        return QbraidJob(**job_data, device=self, client=self.client)

    def try_extracting_info(self, func, error_message):
        """Try to extract information from a function/attribute,
        logging an error if it fails."""
        try:
            return func()
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.info("%s: %s. Field will be omitted in job metadata.", error_message, str(err))
            return None

    def run(
        self,
        run_input: Union[qbraid.programs.QPROGRAM, list[qbraid.programs.QPROGRAM]],
        *args,
        **kwargs,
    ) -> "Union[qbraid.runtime.QbraidJob, list[qbraid.runtime.QbraidJob]]":
        """
        Run a quantum job or a list of quantum jobs on this quantum device.

        Args:
            run_input: A single quantum program or a list of quantum programs to run on the device.

        Returns:
            A QuantumJob object or a list of QuantumJob objects corresponding to the input.

        Raises:
            ValueError: If "num_qubits", "depth", or "openqasm" are included in kwargs.
        """
        forbidden_keys = {"num_qubits", "depth", "openqasm"}
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

        jobs: list[qbraid.runtime.QbraidJob] = []

        for program in run_input_list:
            program_alias = get_program_type_alias(program, safe=True)
            program_spec = ProgramSpec(type(program), alias=program_alias)
            qbraid_program = load_program(program) if program_spec.native else None
            program_data = {
                "num_qubits": None,
                "depth": None,
                "openqasm": None,
            }

            if qbraid_program:
                program_data["num_qubits"] = self.try_extracting_info(
                    lambda program=qbraid_program: program.num_qubits,
                    "Error calculating circuit num_qubits.",
                )
                program_data["depth"] = self.try_extracting_info(
                    lambda program=qbraid_program: program.depth, "Error calculating circuit depth."
                )
                program_data["openqasm"] = self.try_extracting_info(
                    lambda program=program: transpile(program, "qasm3"),
                    "Error converting circuit to OpenQASM 3.",
                )

            self.validate(qbraid_program)
            transpiled_program = self.transpile(program, program_spec)
            transformed_program = self.transform(transpiled_program)
            job = self.submit(transformed_program, *args, **program_data, **kwargs)
            jobs.append(job)

        return jobs[0] if is_single_input else jobs

# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=invalid-name

"""
Module defining abstract QuantumDevice Class

"""
import json
import logging
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid_core.services.quantum import QuantumClient

from qbraid.programs import ProgramSpec, get_program_type_alias, load_program
from qbraid.transpiler import CircuitConversionError, transpile

from .enums import DeviceStatus, DeviceType
from .exceptions import ProgramValidationError, QbraidRuntimeError
from .job import QbraidJob

if TYPE_CHECKING:
    import pyqir
    import qbraid_core.services.quantum

    import qbraid.programs
    import qbraid.runtime
    import qbraid.transpiler


logger = logging.getLogger(__name__)


class QuantumDevice(ABC):
    """Abstract interface for device-like classes."""

    # pylint: disable-next=unused-argument
    def __init__(self, profile: "qbraid.runtime.RuntimeProfile", **kwargs):
        """Create a ``QuantumDevice`` object.

        Args:
            profile (RuntimeProfile): The device runtime profile.

        """
        self._profile = profile
        self._target_spec = profile.get("program_spec")
        self._conversion_graph = profile.get("conversion_graph")

    @property
    def profile(self) -> "qbraid.runtime.RuntimeProfile":
        """Return the runtime profile."""
        return self._profile

    @property
    def id(self) -> str:
        """Return the device ID."""
        return self.profile.get("device_id")

    @property
    def num_qubits(self) -> int:
        """The number of qubits supported by the device."""
        return self.profile.get("num_qubits")

    @property
    def device_type(self) -> "qbraid.runtime.DeviceType":
        """The device type, Simulator, Fake_device or QPU."""
        return DeviceType(self.profile.get("device_type"))

    def __repr__(self):
        """Return a string representation of the device."""
        return f"<{self.__module__}.{self.__class__.__name__}('{self.id}')>"

    @abstractmethod
    def status(self) -> "qbraid.runtime.DeviceStatus":
        """Return device status."""

    @abstractmethod
    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""

    def metadata(self) -> dict[str, Any]:
        """
        Returns a dictionary containing selected metadata about the device.

        The metadata excludes the conversion graph and program specifications, and it includes
        the device's current status and queue depth.

        Returns:
            dict[str, Any]: A dictionary with device status and queue depth among other details.
        """
        # Exclude certain keys from the profile and directly construct the desired dictionary
        metadata = {
            key: value
            for key, value in self.profile.items()
            if key not in ["conversion_graph", "program_spec"]
        }

        try:
            metadata["status"] = self.status().name
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch status: %s", err)
            metadata["status"] = "UNKNOWN"

        try:
            metadata["queue_depth"] = self.queue_depth()
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch queue depth: %s", err)
            metadata["queue_depth"] = None

        return metadata

    def validate(self, program: "Optional[qbraid.programs.QuantumProgram]"):
        """Verifies device status and circuit compatibility.

        Raises:
            ProgramValidationError: If the circuit is incompatible with the device.
        """
        if self.status() != DeviceStatus.ONLINE:
            warnings.warn(
                "Device is not online. Depending on the provider queueing system, "
                "submitting this job may result in an exception or a long wait time.",
                UserWarning,
            )

        if program:
            if self.num_qubits and program.num_qubits > self.num_qubits:
                raise ProgramValidationError(
                    f"Number of qubits in circuit ({program.num_qubits}) exceeds "
                    f"the device's capacity ({self.num_qubits})."
                )
        else:
            logger.info(
                "Skipping qubit count validation: run input program type not supported natively."
            )

    def transpile(
        self, run_input: "qbraid.programs.QPROGRAM", run_input_spec: "qbraid.programs.ProgramSpec"
    ) -> "qbraid.programs.QPROGRAM":
        """Convert circuit to package compatible with target device and pass through any
        provider transpile methods to match topology of device and/or optimize as applicable.

        Returns:
            :data:`~qbraid.programs.QPROGRAM`: Transpiled quantum program (circuit) object

        Raises:
            QbraidRuntimeError: If circuit conversion fails

        """
        if self._target_spec is None:
            logger.info("Skipping transpile: no target ProgramSpec specified in RuntimeProfile.")
            return run_input

        target_alias = self._target_spec.alias
        target_type = self._target_spec.program_type

        if run_input_spec.alias != target_alias:
            try:
                run_input = transpile(
                    run_input, target_alias, conversion_graph=self._conversion_graph
                )
            except CircuitConversionError as err:
                raise QbraidRuntimeError from err

        if not isinstance(run_input, (target_type, type(target_type))):
            raise CircuitConversionError(
                f"Expected transpile step to produce program of type of {target_type}, "
                f"but instead got program of type {type(run_input)}."
            )

        return run_input

    def transform(self, run_input: "qbraid.programs.QPROGRAM") -> "qbraid.programs.QPROGRAM":
        """
        Override this method with any runtime transformations to apply to the run
        input, e.g. circuit optimizations, device-specific gate set conversions, etc.
        Program input type should match output type.

        """
        return run_input

    def apply_runtime_profile(
        self, run_input: "qbraid.programs.QPROGRAM"
    ) -> "qbraid.programs.QPROGRAM":
        """Process quantum program before passing to device run method.

        Returns:
            Transpiled and transformed quantum program
        """
        run_input_alias = get_program_type_alias(run_input, safe=True)
        run_input_spec = ProgramSpec(type(run_input), alias=run_input_alias)
        program = load_program(run_input) if run_input_spec.native else None

        self.validate(program)
        run_input = self.transpile(run_input, run_input_spec)
        run_input = self.transform(run_input)

        return run_input

    @abstractmethod
    def submit(
        self, run_input: "list[qbraid.programs.QPROGRAM]", *args, **kwargs
    ) -> "Union[qbraid.runtime.QuantumJob, list[qbraid.runtime.QuantumJob]]":
        """Vendor run method. Should return dictionary with the following keys."""

    def run(
        self,
        run_input: "Union[qbraid.programs.QPROGRAM, list[qbraid.programs.QPROGRAM]]",
        *args,
        **kwargs,
    ) -> "Union[qbraid.runtime.QuantumJob, list[qbraid.runtime.QuantumJob]]":
        """
        Run a quantum job or a list of quantum jobs on this quantum device.

        Args:
            run_input: A single quantum program or a list of quantum programs to run on the device.

        Returns:
            A QuantumJob object or a list of QuantumJob objects corresponding to the input.
        """
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        run_input_compat = [self.apply_runtime_profile(program) for program in run_input]
        run_input_compat = run_input_compat[0] if is_single_input else run_input_compat
        return self.submit(run_input_compat, *args, **kwargs)


class QbraidDevice(QuantumDevice):
    """Class to represent a qBraid device."""

    def __init__(
        self,
        profile: "qbraid.runtime.RuntimeProfile",
        client: "Optional[qbraid_core.services.quantum.QuantumClient]" = None,
    ):
        """Create a new QbraidDevice object."""
        super().__init__(profile=profile)
        self._client = client or QuantumClient()

    @property
    def client(self) -> QuantumClient:
        """Return the QuantumClient object."""
        return self._client

    def status(self) -> "qbraid.runtime.DeviceStatus":
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
    def create_job(
        self,
        tags: Optional[dict[str, str]] = None,
        shots: Optional[int] = None,
        openqasm: Optional[Union[str, list[str]]] = None,
        bitecode: Optional[Union[bytes, list[bytes]]] = None,
        num_qubits: Optional[Union[int, list[int]]] = None,
        depth: Optional[Union[int, list[int]]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Create new qBraid job.

        Args:
            tags (optional, dict): A dictionary of tags to associate with the job.
            shots (optional, int): The number of shots to run the job for.
            bitecode (optional, bytes or list): The QIR byte code to run.
            openqasm (optional, str or list): The OpenQASM to run.
            num_qubits (optional, int or list): The number of qubits in the circuit.
            depth (optional, int or list): The depth of the circuit.

        Returns:
            The qbraid job ID associated with this job

        """
        tags = tags or {}

        if bitecode is None:
            program_batch = []
        elif isinstance(bitecode, bytes):
            program_batch = [bitecode]
        elif isinstance(bitecode, list) and all(isinstance(item, bytes) for item in bitecode):
            program_batch = bitecode
        else:
            raise ValueError("bitecode must be a bytes object or a list of bytes objects")

        init_data = {
            "bitecode": program_batch,
            "qbraidDeviceId": self.id,
            "shots": shots,
            "tags": json.dumps(tags),
            **kwargs,
        }

        if openqasm:
            if isinstance(openqasm, str):
                init_data["openQasm"] = openqasm
            elif isinstance(openqasm, list):
                init_data["openQasmBatch"] = openqasm
            else:
                raise ValueError("openqasm must be a string or a list of strings")

        if num_qubits:
            if isinstance(num_qubits, int):
                init_data["circuitNumQubits"] = num_qubits
            elif isinstance(num_qubits, list):
                init_data["circuitBatchNumQubits"] = num_qubits
            else:
                raise ValueError("num_qubits must be an integer or a list of integers")

        if depth:
            if isinstance(depth, int):
                init_data["circuitDepth"] = depth
            elif isinstance(depth, list):
                init_data["circuitBatchDepth"] = depth
            else:
                raise ValueError("depth must be an integer or a list of integers")

        return self.client.create_job(data=init_data)

    def _create_and_return_job(
        self,
        module: "pyqir.Module",
        entrypoint: Optional[str] = None,
        shots: Optional[int] = None,
        **kwargs,
    ):
        job_data = self.create_job(
            bitcode=module.bitcode, entrypoint=entrypoint, shots=shots, **kwargs
        )
        job_id = job_data.pop("qbraidJobId")
        return QbraidJob(job_id, device=self, client=self.client, **job_data)

    def submit(
        self,
        run_input: "Union[pyqir.Module, list[pyqir.Module]]",
        *args,
        entrypoint: Optional[str] = None,
        shots: Optional[int] = None,
        **kwargs,
    ) -> "Union[qbraid.runtime.QbraidJob, list[qbraid.runtime.QbraidJob]]":
        """Runs the qir-runner executable with the given QIR file and shots.

        Args:
            run_input (Union[pyqir.Module, list[pyqir.Module,]): QIR module to run in the simulator.
            entrypoint (optional, str): Name of the entrypoint function to execute in the QIR file.
            shots (optional, int): The number of times to repeat the execution of the chosen entry
                                   point in the program. Defaults to 1.

        Returns:
            Union[QbraidJob, list[QbraidJob]: The job object(s) representing the submitted job(s).
        """
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        jobs = [
            self._create_and_return_job(module, entrypoint, shots, **kwargs) for module in run_input
        ]
        if is_single_input:
            return jobs[0]
        return jobs

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
        run_input: "Union[qbraid.programs.QPROGRAM, list[qbraid.programs.QPROGRAM]]",
        *args,
        **kwargs,
    ) -> "Union[qbraid.runtime.job.QbraidJob, list[qbraid.runtime.job.QbraidJob]]":
        """
        Run a quantum job or a list of quantum jobs on this quantum device.

        Args:
            run_input: A single quantum program or a list of quantum programs to run on the device.

        Returns:
            A QuantumJob object or a list of QuantumJob objects corresponding to the input.
        """
        if not isinstance(run_input, list):
            run_input_list = [run_input]
            is_single_input = True
        else:
            run_input_list = run_input
            is_single_input = False

        jobs = []

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
                    lambda program=qbraid_program: self.transpile(program, "qasm3"),
                    "Error converting circuit to OpenQASM 3.",
                )

            self.validate(qbraid_program)
            transpiled_program = self.transpile(program, program_spec)
            transformed_program = self.transform(transpiled_program)
            job = self.submit(transformed_program, **program_data, **kwargs)
            jobs.append(job)

        return jobs[0] if is_single_input else jobs

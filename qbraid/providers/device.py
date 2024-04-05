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
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from qbraid_core.services.quantum import QuantumClient, quantum_lib_proxy_state

from qbraid.programs import get_program_type, load_program
from qbraid.transpiler import CircuitConversionError, transpile

from .enums import DeviceType
from .exceptions import ProgramValidationError, QbraidRuntimeError
from .job import QuantumJob

if TYPE_CHECKING:
    import qbraid.programs
    import qbraid.providers
    import qbraid.transpiler


logger = logging.getLogger(__name__)


class QuantumDevice(ABC):
    """Abstract interface for device-like classes."""

    def __init__(self, device: "qbraid.providers.QDEVICE"):
        """Create a ``QuantumDevice`` object.

        Args:
            device (:data:`~.qbraid.providers.QDEVICE`): qBraid Quantum device object

        """
        # pylint: disable=too-many-function-args
        self._device = device
        self._vendor_id = None
        self._id = None
        self._name = None
        self._vendor = None
        self._provider = None
        self._num_qubits = None
        self._device_type = None
        self._run_package = None
        self._populate_metadata(device)

    @property
    def id(self) -> str:
        """Return the device ID."""
        if self._id is None and self._vendor_id is not None:
            try:
                client = QuantumClient()
                device = client.get_device(vendor_id=self._vendor_id)
                self._id = device["qbraid_id"]
            except Exception as err:  # pylint: disable=broad-exception-caught
                logger.info(
                    "Error retrieving device ID from qBraid API: %s. "
                    "Field will be ommited in job metadata",
                    err,
                )
        return self._id

    @property
    def vendor_id(self) -> str:
        """Return the vendor device ID."""
        return self._vendor_id

    @property
    def name(self) -> str:
        """Return the device name.

        Returns:
            The name of the device.
        """
        return self._name

    @property
    def provider(self) -> str:
        """Return the device provider.

        Returns:
            The provider responsible for the device.

        """
        return self._provider

    @property
    def vendor(self) -> str:
        """Return the software vendor name.

        Returns:
            The name of the software vendor.

        """
        return self._vendor

    @property
    def num_qubits(self) -> int:
        """The number of qubits supported by the device.

        Returns:
            Number of qubits supported by QPU. If Simulator returns None.

        """
        return self._num_qubits

    @property
    def device_type(self) -> "qbraid.providers.DeviceType":
        """The device type, Simulator, Fake_device or QPU.

        Returns:
            Device type enum (SIMULATOR|QPU|FAKE)

        """
        return self._device_type

    @abstractmethod
    def status(self) -> "qbraid.providers.DeviceStatus":
        """Return device status."""

    @abstractmethod
    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""

    @abstractmethod
    def _populate_metadata(self, device: "qbraid.providers.QDEVICE") -> None:
        """Populate device metadata with the following fields:
        * self._id
        * self._vendor_id
        * self._name
        * self._provider
        * self._vendor
        * self._num_qubits
        * self._device_type
        """

    def metadata(self) -> dict:
        """Returns device metadata"""
        return {
            "id": self._id,
            "vendorDeviceId": self._vendor_id,
            "name": self._name,
            "provider": self._provider,
            "vendor": self._vendor,
            "numQubits": self._num_qubits,
            "deviceType": self._device_type.name,
            "status": self.status().name,
            "queueDepth": self.queue_depth(),
        }

    def __str__(self):
        return f"{self.vendor} {self.provider} {self.name} device wrapper"

    def __repr__(self):
        """String representation of a DeviceWrapper object."""
        return f"<{self.__class__.__name__}({self.provider}:'{self.name}')>"

    def verify_run(
        self, run_input: "qbraid.programs.QPROGRAM", safe_mode: bool = False
    ) -> Optional["qbraid.programs.QPROGRAM"]:
        """Verifies device status and circuit compatibility.

        Raises:
            QbraidRuntimeError: If the circuit is incompatible with the device.
        """
        if self.status().value == 1:
            warnings.warn(
                "Device is currently offline. Depending on the provider queueing system, "
                "submitting this job may result in an exception or a long wait time.",
                UserWarning,
            )
        try:
            qbraid_circuit = load_program(run_input)
            if self.num_qubits and qbraid_circuit.num_qubits > self.num_qubits:
                raise ProgramValidationError(
                    f"Number of qubits in circuit ({qbraid_circuit.num_qubits}) exceeds "
                    f"the device's capacity ({self.num_qubits})."
                )
            return qbraid_circuit
        except Exception as err:  # pylint: disable=broad-exception-caught
            if not safe_mode:
                raise
            logger.info("Error verifying run input: %s.", err)
            return None

    def transpile(
        self,
        run_input: "qbraid.programs.QPROGRAM",
        conversion_graph: "Optional[qbraid.transpiler.ConversionGraph]" = None,
    ) -> "qbraid.programs.QPROGRAM":
        """Convert circuit to package compatible with target device and pass through any
        provider transpile methods to match topology of device and/or optimize as applicable.

        Returns:
            :data:`~qbraid.programs.QPROGRAM`: Transpiled quantum program (circuit) object

        Raises:
            QbraidRuntimeError: If circuit conversion fails

        """
        require_supported = conversion_graph is None
        input_run_package = get_program_type(run_input, require_supported=require_supported)
        if input_run_package != self._run_package:
            try:
                run_input = transpile(
                    run_input, self._run_package, conversion_graph=conversion_graph
                )
            except CircuitConversionError as err:
                raise QbraidRuntimeError from err
        return self._transpile(run_input)

    def compile(self, run_input: "qbraid.programs.QPROGRAM") -> "qbraid.programs.QPROGRAM":
        """Compile run input.

        Returns:
            :data:`~qbraid.programs.QPROGRAM`: Compiled quantum program (circuit) object

        Raises:
            QbraidRuntimeError: If circuit conversion fails

        """
        return self._compile(run_input)

    def process_run_input(
        self,
        run_input: "qbraid.programs.QPROGRAM",
        auto_compile: bool = False,
        conversion_graph: "Optional[qbraid.transpiler.ConversionGraph]" = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        """Process quantum program before passing to device run method.

        Returns:
            Tupe of run input and job data dictionary (num_qubits, depth, openqasm string)

        Raises:
            QbraidRuntimeError: If error processing run input

        """
        safe_mode = conversion_graph is not None
        qprogram = self.verify_run(run_input, safe_mode=safe_mode)
        run_input = self.transpile(run_input, conversion_graph=conversion_graph)

        if auto_compile:
            run_input = self._compile(run_input)

        if qprogram is None:
            try:
                qprogram = load_program(run_input)
            except Exception as err:  # pylint: disable=broad-exception-caught
                if not safe_mode:
                    raise
                logger.info("Error loading run input: %s", err)

        def try_extracting_info(lambda_expression, error_message):
            try:
                return lambda_expression()
            except Exception:  # pylint: disable=broad-exception-caught
                logger.info(error_message)
                return None

        num_qubits = try_extracting_info(
            lambda: qprogram.num_qubits,
            "Error calculating circuit num_qubits: %s. Field will be omitted in job metadata",
        )

        depth = try_extracting_info(
            lambda: qprogram.depth,
            "Error calculating circuit depth: %s. Field will be omitted in job metadata",
        )

        openqasm = try_extracting_info(
            lambda: transpile(qprogram.program, "qasm3", conversion_graph=conversion_graph),
            "Error converting circuit to OpenQASM 3: %s. Field will be omitted in job metadata",
        )

        program_data = {
            "num_qubits": num_qubits,
            "depth": depth,
            "openqasm": openqasm,
        }

        return run_input, program_data

    # pylint: disable-next=too-many-arguments
    def create_job(
        self,
        vendor_job_id: str,
        tags: Optional[Dict[str, str]] = None,
        shots: Optional[int] = None,
        openqasm: Optional[Union[str, List[str]]] = None,
        num_qubits: Optional[Union[int, List[int]]] = None,
        depth: Optional[Union[int, List[int]]] = None,
    ) -> Dict[str, Any]:
        """Create new qBraid job.

        Args:
            vendor_job_id: Job ID provided by device vendor
            circuit: Wrapped quantum circuit list
            shots: Number of shots

        Returns:
            The qbraid job ID associated with this job

        """
        tags = tags or {}

        init_data = {
            "vendorJobId": vendor_job_id,
            "qbraidDeviceId": self.id,
            "shots": shots,
            "tags": json.dumps(tags),
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

        if self._device_type == DeviceType("FAKE"):
            init_data["qbraidJobId"] = f"{self.vendor.lower()}_test_id"
            return init_data

        # One of the features of qBraid Quantum Jobs is the ability to send
        # jobs without any credentials using the qBraid Lab platform. If the
        # qBraid Quantum Jobs proxy is enabled, a document has already been
        # created for this job. So, instead creating a duplicate, we query the
        # user jobs for the `vendorJobId` and return the correspondong `qbraidJobId`.
        try:
            jobs_state = quantum_lib_proxy_state(self._run_package)
            jobs_enabled = jobs_state.get("enabled", False)
        except ValueError:
            jobs_enabled = False

        client = QuantumClient()

        if jobs_enabled:
            try:
                return client.get_job(vendor_id=vendor_job_id)
            except IndexError as err:
                raise QbraidRuntimeError(f"{self.vendor} job {vendor_job_id} not found") from err

        return client.create_job(data=init_data)

    @abstractmethod
    def _transpile(self, run_input):
        """Applies any software/device specific modifications to run input."""

    @abstractmethod
    def _compile(self, run_input):
        """Applies any software/device specific modifications to run input."""

    @abstractmethod
    def _run(self, run_input: "qbraid.programs.QPROGRAM", *args, **kwargs) -> Dict[str, Any]:
        """Vendor run method. Should return dictionary with the following keys:

        * "shots" (int): Number of shots. For jobs that don't support shots, set to 0.
        * "tags" (Dict[str, str]): Dictionary of tags. For providers that use list of tags,
                                   set all values to "*".
        * "vendor_job_id" (str): Job ID provided by device vendor.
        * "qbraid_job_obj" (qbraid.providers.QuantumJob): The qBraid Job object to be
                                                          instantiated later. It should
                                                          not be an instance.
        * "vendor_job_obj" (optional, Any): Vendor job object (e.g. braket.aws.AwsQuantumTask).
                                            Optional because should be accessible using
                                            qbraidJobObj.get_job(vendorJobId) anyways,
                                            but eliminates an extra call.
        """

    @abstractmethod
    def _run_batch(
        self, run_input: "List[qbraid.programs.QPROGRAM]", *args, **kwargs
    ) -> Dict[str, Any]:
        """Vendor run method. Should return dictionary with the following keys:

        * "shots" (int): Number of shots. For jobs that don't support shots, set to 0.
        * "tags" (Dict[str, str]): Dictionary of tags. For providers that use list of tags,
                                   set all values to "*".
        * "vendor_job_id" (str): Job ID provided by device vendor.
        * "qbraid_job_obj" (qbraid.providers.QuantumJob): The qBraid Job object to be
                                                          instantiated later. It should
                                                          not be an instance.
        * "vendor_job_obj" (optional, Any): Vendor job object (e.g. braket.aws.AwsQuantumTask).
                                            Optional because should be accessible using
                                            qbraidJobObj.get_job(vendorJobId) anyways,
                                            but eliminates an extra call.
        """

    def process_vendor_job_data(self, vendor_job_data_item, program_data):
        """Process vendor job data and return a QuantumJob object."""
        qbraid_job_obj: Optional[QuantumJob] = vendor_job_data_item.pop("qbraid_job_obj", None)
        vendor_job_obj: Optional[Any] = vendor_job_data_item.pop("vendor_job_obj", None)

        job_data = {**vendor_job_data_item, **program_data}
        job_json = self.create_job(**job_data)
        job_id = job_json.get("qbraidJobId", job_json.get("_id"))

        if qbraid_job_obj is None:
            return QuantumJob.retrieve(job_id)
        return qbraid_job_obj(
            job_id,
            job_obj=vendor_job_obj,
            job_json=job_json,
            device=self,
        )

    def run(
        self,
        run_input: "qbraid.programs.QPROGRAM",
        *args,
        auto_compile: bool = False,
        conversion_graph: "Optional[qbraid.transpiler.ConversionGraph]" = None,
        **kwargs,
    ) -> "qbraid.providers.QuantumJob":
        """Run a quantum job specification on this quantum device.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            conversion_graph (optional, ConversionGraph): Graph of conversion functions to
                                                          apply to the circuit.
            auto_compile (bool): Whether to compile the circuit for the device before running.
                                 Default is False.
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        run_input, program_data = self.process_run_input(
            run_input, auto_compile=auto_compile, conversion_graph=conversion_graph
        )
        vendor_job_data = self._run(run_input, *args, **kwargs)
        return self.process_vendor_job_data(vendor_job_data, program_data)

    def run_batch(
        self,
        run_input: "List[qbraid.programs.QPROGRAM]",
        *args,
        auto_compile: bool = False,
        conversion_graph: "Optional[qbraid.transpiler.ConversionGraph]" = None,
        **kwargs,
    ) -> "Union[qbraid.providers.QuantumJob, List[qbraid.providers.QuantumJob]]":
        """Run a quantum job specification on this quantum device.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            conversion_graph (optional, ConversionGraph): Graph of conversion functions to
                                                          apply to the circuit.
            auto_compile (bool): Whether to compile the circuit for the device before running.
                                 Default is False.
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        program_data_batch = []
        run_input_batch = []
        for program in run_input:
            run_input_transpiled, program_data = self.process_run_input(
                program, auto_compile=auto_compile, conversion_graph=conversion_graph
            )
            run_input_batch.append(run_input_transpiled)
            program_data_batch.append(program_data)
        num_qubits_batch = [data.get("num_qubits") for data in program_data_batch]
        depth_batch = [data.get("depth") for data in program_data_batch]
        openqasm_batch = [data.get("openqasm") for data in program_data_batch]
        program_data = {
            "num_qubits": num_qubits_batch,
            "depth": depth_batch,
            "openqasm": openqasm_batch,
        }
        vendor_job_data = self._run_batch(run_input_batch, *args, **kwargs)

        is_list_input = isinstance(vendor_job_data, list)

        if not is_list_input:
            vendor_job_data = [vendor_job_data]

        qbraid_job_objs = [
            self.process_vendor_job_data(item, program_data) for item in vendor_job_data
        ]

        if is_list_input:
            return qbraid_job_objs
        return qbraid_job_objs[0]

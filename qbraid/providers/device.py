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

import warnings
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING  # pylint: disable=unused-import

from qbraid.api import ApiError, QbraidSession
from qbraid.exceptions import QbraidError
from qbraid.load_program import circuit_wrapper
from qbraid.transpiler.exceptions import CircuitConversionError

from .enums import JobStatus
from .exceptions import ProgramValidationError, QbraidRuntimeError

if TYPE_CHECKING:
    import qbraid


class QuantumDevice(ABC):
    """Abstract interface for device-like classes."""

    def __init__(self, device: "qbraid.QDEVICE"):
        """Create a ``QuantumDevice`` object.

        Args:
            device (:data:`~.qbraid.QDEVICE`): qBraid Quantum device object

        """
        # pylint: disable=too-many-function-args
        self._device = device
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
        return self._id

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
        """The device type, Simulator or QPU.

        Returns:
            Device type enum (Simulator|QPU)

        """
        return self._device_type

    @abstractmethod
    def status(self) -> "qbraid.providers.DeviceStatus":
        """Return device status."""

    @abstractmethod
    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""

    @abstractmethod
    def _populate_metadata(self, device: "qbraid.QDEVICE") -> None:
        """Populate device metadata with the following fields:
        * self._id
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

    def verify_run(self, run_input: "qbraid.QPROGRAM") -> None:
        """Checks device is online and that circuit num qubits <= device num qubits.

        Raises:
            QbraidRuntimeError: If error applying circuit wrapper or circuit number of
                qubits exceeds device number qubits

        """
        if self.status().value == 1:
            warnings.warn(
                "Device is currently offline. Depending on the provider queueing system, "
                "submitting this job may result in an exception or a long wait time.",
                UserWarning,
            )

        try:
            qbraid_circuit = circuit_wrapper(run_input)
        except QbraidError as err:
            raise ProgramValidationError from err

        if self.num_qubits and qbraid_circuit.num_qubits > self.num_qubits:
            raise ProgramValidationError(
                f"Number of qubits in circuit ({qbraid_circuit.num_qubits}) exceeds "
                f"number of qubits in device ({self.num_qubits})."
            )

    def transpile(self, run_input: "qbraid.QPROGRAM") -> "qbraid.QPROGRAM":
        """Convert circuit to package compatible with target device and pass through any
        provider transpile methods to match topology of device and/or optimize as applicable.

        Returns:
            :data:`~qbraid.QPROGRAM`: Transpiled quantum program (circuit) object

        Raises:
            QbraidRuntimeError: If circuit conversion fails

        """
        input_run_package = run_input.__module__.split(".")[0]
        if input_run_package != self._run_package:
            qbraid_circuit = circuit_wrapper(run_input)
            try:
                run_input = qbraid_circuit.transpile(self._run_package)
            except CircuitConversionError as err:
                raise QbraidRuntimeError from err
        return self._transpile(run_input)

    def compile(self, run_input: "qbraid.QPROGRAM") -> "qbraid.QPROGRAM":
        """Compile run input.

        Returns:
            :data:`~qbraid.QPROGRAM`: Compiled quantum program (circuit) object

        Raises:
            QbraidRuntimeError: If circuit conversion fails

        """
        return self._compile(run_input)

    def process_run_input(
        self, run_input: "qbraid.QPROGRAM", auto_compile: bool = False
    ) -> "qbraid.transpiler.QuantumProgram":
        """Process quantum program before passing to device run method.

        Returns:
            :class:`~qbraid.transpiler.QuantumProgram`: qBraid wrapped quantum program object

        Raises:
            QbraidRuntimeError: If error processing run input

        """
        self.verify_run(run_input)
        run_input = self.transpile(run_input)
        if auto_compile:
            run_input = self._compile(run_input)
        return circuit_wrapper(run_input)

    def _init_job(
        self,
        vendor_job_id: str,
        circuits: "qbraid.transpiler.QuantumProgram",
        shots: int,
    ) -> str:
        """Initialize data dictionary for new qbraid job and
        create associated MongoDB job document.

        Args:
            vendor_job_id: Job ID provided by device vendor
            circuit: Wrapped quantum circuit list
            shots: Number of shots

        Returns:
            The qbraid job ID associated with this job

        """
        session = QbraidSession()

        vendor = self.vendor.lower()
        # One of the features of qBraid Quantum Jobs is the ability to send
        # jobs without any credentials using the qBraid Lab platform. If the
        # qBraid Quantum Jobs proxy is enabled, a document has already been
        # created for this job. So, instead creating a duplicate, we query the
        # user jobs for the `vendorJobId` and return the correspondong `qbraidJobId`.
        if session._running_in_lab() and session._qbraid_jobs_enabled(vendor):
            try:
                job = session.post("/get-user-jobs", json={"vendorJobId": vendor_job_id}).json()[0]
                return job["qbraidJobId"]
            except IndexError as err:
                raise ApiError(f"{self.vendor} job {vendor_job_id} not found") from err

        # get qBraid device ID. Temporary workaround until we have a better way
        qbraid_id = session.get("/public/lab/get-devices", params={"objArg": self.id}).json()[0][
            "qbraid_id"
        ]

        # Create a new document for the user job. The qBraid API creates a unique
        # Job ID, which is collected in the response. We use dummy variables for
        # each of the status fields, which will be updated via the `get_job_data`
        # function upon instantiation of the `QuantumJob` object.
        init_data = {
            "qbraidJobId": "",
            "vendorJobId": vendor_job_id,
            "qbraidDeviceId": qbraid_id,
            "vendorDeviceId": self.id,
            "shots": shots,
            "createdAt": datetime.utcnow(),
            "status": "UNKNOWN",  # this will be set after we get back the job ID and check status
            "qbraidStatus": JobStatus.INITIALIZING.name,
            "email": session.user_email,
        }

        if len(circuits) == 1:
            init_data["circuitNumQubits"] = circuits[0].num_qubits
            init_data["circuitDepth"]: circuits[0].depth
        else:
            init_data["circuitBatchNumQubits"] = ([circuit.num_qubits for circuit in circuits],)
            init_data["circuitBatchDepth"] = [circuit.depth for circuit in circuits]

        return session.post("/init-job", data=init_data).json()

    @abstractmethod
    def _transpile(self, run_input):
        """Applies any software/device specific modifications to run input."""

    @abstractmethod
    def _compile(self, run_input):
        """Applies any software/device specific modifications to run input."""

    @abstractmethod
    def run(self, run_input: "qbraid.QPROGRAM", *args, **kwargs) -> "qbraid.providers.QuantumJob":
        """Abstract run method."""

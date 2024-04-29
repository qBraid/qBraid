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

from qbraid.programs import get_program_type_alias, load_program
from qbraid.programs._import import NATIVE_REGISTRY
from qbraid.transpiler import CircuitConversionError, transpile

from .enums import DeviceStatus, DeviceType
from .exceptions import ProgramValidationError, QbraidRuntimeError
from .profile import RuntimeProfile

if TYPE_CHECKING:
    import qbraid.programs
    import qbraid.runtime
    import qbraid.transpiler


logger = logging.getLogger(__name__)


class QuantumDevice(ABC):
    """Abstract interface for device-like classes."""

    def __init__(self, device_id: str, provider: "qbraid.runtime.QuantumProvider" = None):
        """Create a ``QuantumDevice`` object.

        Args:
            device_id: The unique identifier of the device.
            provider: The provider associated with the device.

        """
        self._id = device_id
        self._provider = provider
        self._profile: RuntimeProfile = self._default_profile()

    @property
    def id(self) -> str:
        """Return the device ID."""
        return self._id

    @property
    def num_qubits(self) -> int:
        """The number of qubits supported by the device.

        Returns:
            Number of qubits supported by QPU. If Simulator returns None.

        """
        return self._profile.get("num_qubits")

    @property
    def device_type(self) -> "qbraid.runtime.DeviceType":
        """The device type, Simulator, Fake_device or QPU.

        Returns:
            Device type enum (SIMULATOR|QPU|FAKE)

        """
        return self._profile.get("device_type")

    @abstractmethod
    def status(self) -> "qbraid.runtime.DeviceStatus":
        """Return device status."""

    @abstractmethod
    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""

    @classmethod
    @abstractmethod
    def _default_profile(cls):
        """Return the default runtime profile

        This method will return a :class:`qbraid.runtime.RuntimeProfile`
        subclass object that will be used for the default options. These
        should be the default parameters to use for the options of the
        device runtime protocol.

        Returns:
            qbraid.runtime.RuntimeProfile: A profile object with default values set
        """

    def metadata(self) -> dict[str, Any]:
        """Returns device metadata"""
        return {
            "id": self.id,
            "numQubits": self.num_qubits,
            "deviceType": self.device_type.name,
            "status": self.status().name,
            "queueDepth": self.queue_depth(),
        }

    def __str__(self):
        """Official string representation of QuantumDevice object."""
        return f"<{self.__class__.__name__}('{self.id}')>"

    def validate(self, run_input: "qbraid.programs.QPROGRAM"):
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

        run_input_type = self._profile.get("run_input_program_type")
        run_input_alias = self._profile.get("run_input_type_alias")

        if not isinstance(run_input, (run_input_type, type(run_input_type))):
            raise ProgramValidationError(
                f"Expected program of type {run_input_type}, but got program of type {type(run_input)}."
            )

        if run_input_alias in NATIVE_REGISTRY:
            qbraid_circuit = load_program(run_input)
            if self.num_qubits and qbraid_circuit.num_qubits > self.num_qubits:
                raise ProgramValidationError(
                    f"Number of qubits in circuit ({qbraid_circuit.num_qubits}) exceeds "
                    f"the device's capacity ({self.num_qubits})."
                )
        else:
            logger.info(
                "Run input program type not supported natively: skipping qubit count validation."
            )

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
        target_type_alias = self._profile.get("run_input_type_alias")
        input_run_input_alias = get_program_type_alias(run_input)
        if input_run_input_alias != target_type_alias:
            try:
                run_input = transpile(
                    run_input, target_type_alias, conversion_graph=conversion_graph
                )
            except CircuitConversionError as err:
                raise QbraidRuntimeError from err
        return run_input

    def transform(self, run_input: "qbraid.programs.QPROGRAM") -> "qbraid.programs.QPROGRAM":
        """
        Override this method with any runtime transformations to apply to the run
        input, e.g. circuit optimizations, device-specific gate set conversions, etc.
        Program input type should match output type.

        """
        return run_input

    def apply_runtime_profile(
        self,
        run_input: "qbraid.programs.QPROGRAM",
        conversion_graph: "Optional[qbraid.transpiler.ConversionGraph]" = None,
    ) -> "qbraid.programs.QPROGRAM":
        """Process quantum program before passing to device run method.

        Returns:
            Transpiled and transformed quantum program
        """
        self.validate(run_input)
        run_input = self.transpile(run_input, conversion_graph=conversion_graph)
        run_input = self.transform(run_input)

        return run_input

    @abstractmethod
    def submit(self, run_input: "qbraid.programs.QPROGRAM", *args, **kwargs) -> dict[str, Any]:
        """Vendor run method. Should return dictionary with the following keys."""

    @abstractmethod
    def submit_batch(
        self, run_input: "list[qbraid.programs.QPROGRAM]", *args, **kwargs
    ) -> dict[str, Any]:
        """Vendor run method. Should return dictionary with the following keys."""

    def run(
        self,
        run_input: "qbraid.programs.QPROGRAM",
        *args,
        conversion_graph: "Optional[qbraid.transpiler.ConversionGraph]" = None,
        **kwargs,
    ) -> "qbraid.runtime.Job":
        """Run a quantum job specification on this quantum device.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            conversion_graph (optional, ConversionGraph): Graph of conversion functions to
                                                          apply to the circuit.
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        run_input, _ = self.process_run_input(run_input, conversion_graph=conversion_graph)
        return self.submit(run_input, *args, **kwargs)

    def run_batch(
        self,
        run_input: "list[qbraid.programs.QPROGRAM]",
        *args,
        conversion_graph: "Optional[qbraid.transpiler.ConversionGraph]" = None,
        **kwargs,
    ) -> "Union[qbraid.runtime.QuantumJob, list[qbraid.runtime.QuantumJob]]":
        """Run a quantum job specification on this quantum device.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            conversion_graph (optional, ConversionGraph): Graph of conversion functions to
                                                          apply to the circuit.
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        program_data_batch = []
        run_input_batch = []
        for program in run_input:
            run_input_transpiled, program_data = self.process_run_input(
                program, conversion_graph=conversion_graph
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
        return self.submit_batch(run_input_batch, *args, **kwargs)

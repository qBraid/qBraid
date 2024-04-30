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
import logging
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Union

from qbraid.programs import get_program_type_alias, load_program
from qbraid.programs._import import NATIVE_REGISTRY
from qbraid.transpiler import CircuitConversionError, transpile

from .enums import DeviceStatus
from .exceptions import ProgramValidationError, QbraidRuntimeError

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
            device_id (str): The unique identifier of the device.
            provider (QuantumProvider, optional): The provider associated with the device.

        """
        self._id = device_id
        self._provider = provider
        self._profile = None

    @property
    def id(self) -> str:
        """Return the device ID."""
        return self._id

    @property
    def num_qubits(self) -> int:
        """The number of qubits supported by the device."""
        return self.profile.get("num_qubits")

    @property
    def device_type(self) -> "qbraid.runtime.DeviceType":
        """The device type, Simulator, Fake_device or QPU."""
        return self.profile.get("device_type")

    @abstractmethod
    def status(self) -> "qbraid.runtime.DeviceStatus":
        """Return device status."""

    @abstractmethod
    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""

    @property
    def profile(self) -> "qbraid.runtime.RuntimeProfile":
        """Return the runtime profile."""
        if not self._profile:
            self._profile = self._default_profile()
        return self._profile

    @abstractmethod
    def _default_profile(self):
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

        run_input_type = self.profile.get("run_input_program_type")
        run_input_alias = self.profile.get("run_input_type_alias")

        if not isinstance(run_input, (run_input_type, type(run_input_type))):
            raise ProgramValidationError(
                f"Expected program of type {run_input_type}, "
                f"but got program of type {type(run_input)}."
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

    def transpile(self, run_input: "qbraid.programs.QPROGRAM") -> "qbraid.programs.QPROGRAM":
        """Convert circuit to package compatible with target device and pass through any
        provider transpile methods to match topology of device and/or optimize as applicable.

        Returns:
            :data:`~qbraid.programs.QPROGRAM`: Transpiled quantum program (circuit) object

        Raises:
            QbraidRuntimeError: If circuit conversion fails

        """
        conversion_graph = self.profile.get("conversion_graph")
        target_type_alias = self.profile.get("run_input_type_alias")
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
        self, run_input: "qbraid.programs.QPROGRAM"
    ) -> "qbraid.programs.QPROGRAM":
        """Process quantum program before passing to device run method.

        Returns:
            Transpiled and transformed quantum program
        """
        self.validate(run_input)
        run_input = self.transpile(run_input)
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
        return self.submit(run_input_compat, *args, **kwargs)

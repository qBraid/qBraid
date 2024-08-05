# Copyright (C) 2024 qBraid
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
from __future__ import annotations

import logging
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from qbraid.programs import ProgramSpec, get_program_type_alias, load_program
from qbraid.transpiler import CircuitConversionError, ConversionGraph, ConversionScheme, transpile

from .enums import DeviceStatus
from .exceptions import ProgramValidationError, QbraidRuntimeError, ResourceNotFoundError

if TYPE_CHECKING:
    import qbraid.programs
    import qbraid.runtime
    import qbraid.transpiler


logger = logging.getLogger(__name__)


class QuantumDevice(ABC):
    """Abstract interface for quantum devices."""

    def __init__(  # pylint: disable-next=unused-argument
        self,
        profile: qbraid.runtime.TargetProfile,
        scheme: Optional[ConversionScheme] = None,
        **kwargs,
    ):
        """Create a ``QuantumDevice`` object.

        Args:
            profile (TargetProfile): The device runtime profile.
            scheme (Optional[ConversionScheme]): The conversion graph and options passed
                                                 to the transpiler at runtime.

        """
        self._profile = profile
        self._target_spec: Optional[ProgramSpec] = profile.program_spec
        self._scheme = scheme or ConversionScheme()

    @property
    def profile(self) -> qbraid.runtime.TargetProfile:
        """Return the runtime profile."""
        return self._profile

    @property
    def id(self) -> str:
        """Return the device ID."""
        return self.profile.device_id

    @property
    def num_qubits(self) -> Optional[int]:
        """The number of qubits supported by the device."""
        return self.profile.num_qubits

    @property
    def simulator(self) -> bool:
        """The device type, Simulator, Fake_device or QPU."""
        return self.profile.simulator

    @property
    def scheme(self) -> ConversionScheme:
        """Return the conversion scheme."""
        if not self._scheme.conversion_graph:
            self._scheme.update_values(conversion_graph=ConversionGraph())
        return self._scheme

    def __repr__(self):
        """Return a string representation of the device."""
        return f"<{self.__module__}.{self.__class__.__name__}('{self.id}')>"

    @abstractmethod
    def status(self) -> qbraid.runtime.DeviceStatus:
        """Return device status."""

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""
        raise ResourceNotFoundError("Queue depth is not available for this device.")

    def update_scheme(self, **kwargs):
        """Update the conversion scheme with new values."""
        self._scheme.update_values(**kwargs)

    def metadata(self) -> dict[str, Any]:
        """
        Returns a dictionary containing selected metadata about the device.

        The metadata excludes the program specifications, and it includes
        the device's current status and queue depth.

        Returns:
            dict[str, Any]: A dictionary with device status and queue depth among other details.
        """
        # Exclude certain keys from the profile and directly construct the desired dictionary
        metadata = {key: value for key, value in self.profile if key != "program_spec"}

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

    def validate(self, program: Optional[qbraid.programs.QuantumProgram]):
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
        self, run_input: qbraid.programs.QPROGRAM, run_input_spec: qbraid.programs.ProgramSpec
    ) -> qbraid.programs.QPROGRAM:
        """Convert circuit to package compatible with target device and pass through any
        provider transpile methods to match topology of device and/or optimize as applicable.

        Returns:
            :data:`~qbraid.programs.QPROGRAM`: Transpiled quantum program (circuit) object

        Raises:
            QbraidRuntimeError: If circuit conversion fails

        """
        if self._target_spec is None:
            logger.info("Skipping transpile: no target ProgramSpec specified in TargetProfile.")
            return run_input

        target_alias = self._target_spec.alias
        target_type = self._target_spec.program_type

        if run_input_spec.alias != target_alias:
            kwargs = self.scheme.to_dict()
            try:
                run_input = transpile(run_input, target_alias, **kwargs)
            except CircuitConversionError as err:
                raise QbraidRuntimeError from err

        if not (
            isinstance(run_input, list)
            and all(
                isinstance(item, (target_type, type(target_type))) for item in cast(list, run_input)
            )
        ) and not isinstance(run_input, (target_type, type(target_type))):
            raise CircuitConversionError(
                f"Expected transpile step to produce program of type of {target_type}, "
                f"but instead got program of type {type(run_input)}."
            )

        return run_input

    def transform(self, run_input: qbraid.programs.QPROGRAM) -> qbraid.programs.QPROGRAM:
        """
        Override this method with any runtime transformations to apply to the run
        input, e.g. circuit optimizations, device-specific gate set conversions, etc.
        Program input type should match output type.

        """
        return run_input

    def apply_runtime_profile(
        self, run_input: qbraid.programs.QPROGRAM
    ) -> qbraid.programs.QPROGRAM:
        """Process quantum program before passing to device run method.

        Returns:
            Transpiled and transformed quantum program
        """
        if self._target_spec is not None:
            run_input_alias = get_program_type_alias(run_input, safe=True)
            run_input_spec = ProgramSpec(type(run_input), alias=run_input_alias)
            program = load_program(run_input) if run_input_spec.native else None

            self.validate(program)
            run_input = self.transpile(run_input, run_input_spec)

        is_single_output = not isinstance(run_input, list)
        run_input = [run_input] if is_single_output else run_input
        run_input = [self.transform(p) for p in cast(list, run_input)]
        run_input = run_input[0] if is_single_output else run_input
        return run_input

    @abstractmethod
    def submit(
        self,
        run_input: Union[qbraid.programs.QPROGRAM, list[qbraid.programs.QPROGRAM]],
        *args,
        **kwargs,
    ) -> Union[qbraid.runtime.QuantumJob, list[qbraid.runtime.QuantumJob]]:
        """Vendor run method. Should return dictionary with the following keys."""

    def run(
        self,
        run_input: Union[qbraid.programs.QPROGRAM, list[qbraid.programs.QPROGRAM]],
        *args,
        **kwargs,
    ) -> Union[qbraid.runtime.QuantumJob, list[qbraid.runtime.QuantumJob]]:
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

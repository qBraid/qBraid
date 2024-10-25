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

import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from qbraid._logging import logger
from qbraid.programs import ProgramLoaderError, ProgramSpec, get_program_type_alias, load_program
from qbraid.transpiler import CircuitConversionError, ConversionGraph, ConversionScheme, transpile

from .enums import DeviceStatus, ValidationLevel
from .exceptions import ProgramValidationError, QbraidRuntimeError, ResourceNotFoundError
from .options import RuntimeOptions

if TYPE_CHECKING:
    import qbraid.programs
    import qbraid.runtime
    import qbraid.transpiler


class QuantumDevice(ABC):
    """Abstract interface for quantum devices."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        scheme: Optional[ConversionScheme] = None,
        options: Optional[RuntimeOptions] = None,
    ):
        """Create a ``QuantumDevice`` object.

        Args:
            profile (TargetProfile): The device runtime profile.
            scheme (Optional[ConversionScheme]): The conversion graph and options passed
                to the transpiler at runtime.
            options (Optional[RuntimeOptions]): Custom options to control the runtime
                behavior. Adds fields or overrides default values for ``transpile``,
                ``transform``, and ``validate``. Note that while you can modify these
                values, their associated validators are fixed and cannot be changed.
        """
        self._profile = profile
        self._target_spec: Optional[ProgramSpec] = profile.program_spec
        self._scheme = scheme or ConversionScheme()
        self._options = self._default_options()
        if options:
            self._options.merge(options, override_validators=False)

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

    @classmethod
    def _default_options(cls) -> RuntimeOptions:
        """Define default options for the QuantumDevice."""
        options = RuntimeOptions(transpile=True, transform=True, validate=ValidationLevel.RAISE)

        # pylint: disable=unnecessary-lambda
        options.set_validator("transpile", lambda x: isinstance(x, bool))
        options.set_validator("transform", lambda x: isinstance(x, bool))
        options.set_validator(
            "validate",
            lambda x: isinstance(x, ValidationLevel) or (isinstance(x, int) and 0 <= x <= 2),
        )

        # pylint: enable=unnecessary-lambda

        return options

    def set_options(self, **fields):
        """
        Update the runtime options for the QuantumDevice.

        The runtime options control the default behavior of the `QuantumDevice.run` method,
        including settings such as transpilation, verification, and transformation. If an
        unsupported option is provided, an `AttributeError` will be raised.

        Args:
            **fields: Keyword arguments representing the runtime options to update.
                    The options must already exist in the device's configuration.

        Raises:
            AttributeError: If an invalid runtime option is passed.
        """
        for field in fields:
            if not hasattr(self._options, field):
                raise AttributeError(f"Options field '{field}' is not valid for this device")
        self._options.update_options(**fields)

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the device."""
        raise ResourceNotFoundError("Queue depth is not available for this device.")

    def avg_queue_time(self) -> int:
        """Return the average time (in seconds) a job spends in the queue for the device."""
        raise ResourceNotFoundError("Average queue time is not available for this device.")

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
        metadata = self.profile.model_dump(
            exclude=["program_spec", "experiment_type", "noise_models"]
        )

        try:
            metadata["queue_depth"] = self.queue_depth()
        except ResourceNotFoundError as err:
            logger.info("Queue depth data not available: %s", err)

        try:
            metadata["average_queue_time"] = self.avg_queue_time()
        except ResourceNotFoundError as err:
            logger.info("Average queue time data not available: %s", err)

        metadata["status"] = self.status().name
        metadata["paradigm"] = (
            self.profile.experiment_type.value if self.profile.experiment_type else None
        )

        if self.simulator is True:
            metadata["noise_models"] = (
                list(self.profile.noise_models) if self.profile.noise_models else None
            )

        options = {
            key: (value.value if isinstance(value, ValidationLevel) else value)
            for key, value in dict(self._options).items()
        }

        program_spec = self.profile.program_spec
        runtime_config = {
            "target_ir": program_spec.alias if program_spec else None,
            "conversion_scheme": self._scheme.to_dict(),
            "options": options,
        }

        metadata["runtime_config"] = runtime_config

        return metadata

    def validate(self, run_input: qbraid.programs.QPROGRAM) -> None:
        """Verifies run input compatibility with target device.

        Raises:
            ProgramValidationError: If the run input is incompatible with the target device.
        """
        level = ValidationLevel(self._options.get("validate", 0))

        if level == ValidationLevel.NONE:
            return None

        if self.status() != DeviceStatus.ONLINE:
            warnings.warn(
                "Device is not online. Submitting this job may result in an exception "
                "or a long wait time.",
                UserWarning,
            )

        try:
            program = load_program(run_input)
        except ProgramLoaderError:
            logger.info(
                "Skipping qubit count validation: program type '%s' not supported natively.",
                type(run_input).__name__,
            )
        else:
            if self.num_qubits and program.num_qubits > self.num_qubits:
                message = (
                    f"Number of qubits in the circuit ({program.num_qubits}) exceeds "
                    f"the device's capacity ({self.num_qubits})."
                )
                if level == ValidationLevel.RAISE:
                    raise ProgramValidationError(message)
                if level == ValidationLevel.WARN:
                    warnings.warn(message, UserWarning)

        if self._target_spec is None:
            return None

        try:
            self._target_spec.validate(run_input)
        except ValueError as err:
            if level == ValidationLevel.RAISE:
                raise ProgramValidationError from err
            if level == ValidationLevel.WARN:
                warnings.warn(str(err), UserWarning)

        return None

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
        if self._target_spec is None:
            return run_input

        run_input_ir = self._target_spec.to_ir(run_input)
        return run_input_ir

    def apply_runtime_profile(
        self, run_input: qbraid.programs.QPROGRAM
    ) -> qbraid.programs.QPROGRAM:
        """Process quantum program before passing to device run method.

        Returns:
            Transpiled and transformed quantum program
        """
        if self._target_spec is not None and self._options.get("transpile") is True:
            run_input_alias = get_program_type_alias(run_input, safe=True)
            run_input_spec = ProgramSpec(type(run_input), alias=run_input_alias)
            run_input = self.transpile(run_input, run_input_spec)

        self.validate(run_input)
        is_single_output = not isinstance(run_input, list)
        run_input = [run_input] if is_single_output else run_input

        if self._options.get("transform") is True:
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

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
from qbraid.programs import (
    ProgramLoaderError,
    ProgramSpec,
    ProgramTypeError,
    get_program_type_alias,
    load_program,
)
from qbraid.transpiler import (
    ConversionGraph,
    ConversionPathNotFoundError,
    ConversionScheme,
    ProgramConversionError,
    transpile,
)

from .enums import DeviceStatus, ValidationLevel
from .exceptions import ProgramValidationError, ResourceNotFoundError
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
        self._target_spec: Optional[Union[ProgramSpec, list[ProgramSpec]]] = profile.program_spec
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
            self._scheme.update_values(conversion_graph=ConversionGraph(include_isolated=True))
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
        options = RuntimeOptions(
            transpile=True, transform=True, validate=ValidationLevel.RAISE, prepare=True
        )

        # pylint: disable=unnecessary-lambda
        options.set_validator("transpile", lambda x: isinstance(x, bool))
        options.set_validator("transform", lambda x: isinstance(x, bool))
        options.set_validator(
            "validate",
            lambda x: isinstance(x, ValidationLevel) or (isinstance(x, int) and 0 <= x <= 2),
        )
        options.set_validator("prepare", lambda x: isinstance(x, bool))

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
        for field, value in fields.items():
            if not hasattr(self._options, field):
                raise AttributeError(f"Options field '{field}' is not valid for this device")
            if field == "validate" and isinstance(
                value, bool
            ):  # TODO: Move this to the RuntimeOptions class
                fields[field] = ValidationLevel.RAISE if value else ValidationLevel.NONE
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
            logger.info(err)

        try:
            metadata["average_queue_time"] = self.avg_queue_time()
        except ResourceNotFoundError as err:
            logger.info(err)

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

        program_spec = self._target_spec

        if not program_spec:
            target_program_type = None
        elif isinstance(program_spec, list):
            target_program_type = [ps.alias for ps in program_spec]
        else:
            target_program_type = program_spec.alias

        runtime_config = {
            "target_program_type": target_program_type,
            "conversion_scheme": self._scheme.to_dict(),
            "options": options,
        }

        metadata["runtime_config"] = runtime_config

        return metadata

    def set_target_program_type(self, alias: str | list[str] | None) -> None:
        """Set the program type to target during runtime transpile step.

        Args:
            alias: The alias(es) of the target program spec(s) to set.

        Raises:
            ValueError: If the given alias does not match any program spec in the target profile.
        """
        if alias is None:
            self._target_spec = None
            return

        aliases = [alias] if isinstance(alias, str) else alias

        if len(set(aliases)) != len(aliases):
            raise ValueError("Duplicate aliases are not allowed.")

        if isinstance(self.profile.program_spec, list):
            spec_aliases = {spec.alias for spec in self.profile.program_spec}
            if isinstance(alias, str):
                if alias not in spec_aliases:
                    raise ValueError(
                        f"Invalid alias: '{alias}'. Available aliases: {', '.join(spec_aliases)}"
                    )
                self._target_spec = next(
                    spec for spec in self.profile.program_spec if spec.alias == alias
                )
            else:
                missing_aliases = [a for a in aliases if a not in spec_aliases]
                if missing_aliases:
                    raise ValueError(
                        f"Invalid aliases: {', '.join(missing_aliases)}. "
                        f"Available aliases: {', '.join(spec_aliases)}"
                    )
                self._target_spec = [
                    spec for spec in self.profile.program_spec if spec.alias in aliases
                ]

        elif self.profile.program_spec is not None:
            if len(aliases) != 1:
                raise ValueError(
                    "Alias list must contain exactly one alias when the target profile "
                    "has a single program spec."
                )
            as_lst = isinstance(alias, list)
            alias = aliases[0]
            if alias != self.profile.program_spec.alias:
                raise ValueError(
                    f"Invalid alias: '{alias}'. "
                    f"Available aliases: '{self.profile.program_spec.alias}'"
                )
            self._target_spec = [self.profile.program_spec] if as_lst else self.profile.program_spec

        else:
            raise ValueError("Target profile has no program spec defined.")

    def _get_target_spec(self, run_input: qbraid.programs.QPROGRAM) -> ProgramSpec:
        run_input_alias = get_program_type_alias(run_input, safe=True)
        target_specs = (
            self._target_spec
            if isinstance(self._target_spec, list)
            else [self._target_spec] if self._target_spec else []
        )

        for target_spec in target_specs:
            if target_spec.alias == run_input_alias:
                return target_spec

        raise ProgramTypeError(
            message=f"Could not find a target ProgramSpec matching the alias '{run_input_alias}'."
        )

    def transpile(
        self,
        run_input: qbraid.programs.QPROGRAM,
        run_input_spec: qbraid.programs.ProgramSpec,
    ) -> qbraid.programs.QPROGRAM:
        """Convert circuit to package compatible with target device and pass through any
        provider transpile methods to match topology of device and/or optimize as applicable.

        Returns:
            :data:`~qbraid.programs.QPROGRAM`: Transpiled quantum program

        Raises:
            ProgramConversionError: If program conversion fails

        """
        if not self._target_spec:
            logger.info("Skipping transpile: no target ProgramSpec specified in TargetProfile.")
            return run_input

        graph = self.scheme.conversion_graph
        target_specs = (
            self._target_spec if isinstance(self._target_spec, list) else [self._target_spec]
        )

        alias_to_spec = {target_spec.alias: target_spec for target_spec in target_specs}
        ordered_targets = graph.get_sorted_closest_targets(
            run_input_spec.alias, list(alias_to_spec.keys())
        )
        ordered_target_specs = [alias_to_spec[alias] for alias in ordered_targets]

        cached_errors = []
        conversion_scheme_fields = self.scheme.to_dict()

        for target_spec in ordered_target_specs:
            target_alias = target_spec.alias
            target_type = target_spec.program_type

            if run_input_spec.alias == target_alias:
                return run_input

            logger.debug(
                "Transpiling '%s' program to device target program type '%s'",
                run_input_spec.alias,
                target_alias,
            )

            try:
                transpiled_run_input = transpile(
                    run_input, target_alias, **conversion_scheme_fields
                )

                if not (
                    isinstance(transpiled_run_input, list)
                    and all(
                        isinstance(item, (target_type, type(target_type)))
                        for item in cast(list, transpiled_run_input)
                    )
                ) and not isinstance(transpiled_run_input, (target_type, type(target_type))):
                    raise ProgramConversionError(
                        f"Expected transpile step to produce program of type of {target_type}, "
                        f"but instead got program of type {type(transpiled_run_input)}."
                    )

                return transpiled_run_input
            except (ProgramConversionError, ConversionPathNotFoundError) as err:
                cached_errors.append(err)

        if len(cached_errors) == 1:
            raise cached_errors[0]

        error_messages = "\n".join([str(error) for error in cached_errors])
        raise ProgramConversionError(
            "Transpile step failed after multiple attempts. "
            f"The following errors occurred:\n{error_messages}"
        )

    def transform(self, run_input: qbraid.programs.QPROGRAM) -> qbraid.programs.QPROGRAM:
        """
        Override this method with any runtime transformations to apply to the run
        input, e.g. circuit optimizations, device-specific gate set conversions, etc.
        Program input type should match output type.

        """
        return run_input

    def validate(
        self, run_input_batch: list[qbraid.programs.QPROGRAM], suppress_device_warning: bool = False
    ) -> None:
        """Verifies run input compatibility with target device.

        Raises:
            ProgramValidationError: If the run input is incompatible with the target device.
        """
        level = ValidationLevel(self._options.get("validate", 0))

        logger.debug("Validating run input for device at %s", level)

        if level == ValidationLevel.NONE:
            return None

        if not suppress_device_warning and self.status() != DeviceStatus.ONLINE:
            warnings.warn(
                "Device is not online. Submitting this job may result in an exception "
                "or a long wait time.",
                UserWarning,
            )

        for run_input in run_input_batch:
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
                continue

            target_spec = self._get_target_spec(run_input)

            try:
                target_spec.validate(run_input)
            except ValueError as err:
                if level == ValidationLevel.RAISE:
                    raise ProgramValidationError(err) from err
                if level == ValidationLevel.WARN:
                    warnings.warn(str(err), UserWarning)

        return None

    def prepare(self, run_input: qbraid.programs.QPROGRAM) -> Any:
        """Convert the quantum program to an intermediate representation (IR) compatible
        with the submission format required for the target device and its provider API."""
        if self._target_spec is None or not self._options.get("prepare"):
            return run_input

        logger.debug("Preparing (i.e. serializing) run input")

        target_spec = self._get_target_spec(run_input)
        return target_spec.serialize(run_input)

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

        is_single_output = not isinstance(run_input, list)
        run_input = [run_input] if is_single_output else run_input

        if self._options.get("transform") is True:
            logger.debug("Applying device-specific transformations (no-op in base class)")
            run_input = [self.transform(p) for p in cast(list, run_input)]

        self.validate(run_input)

        run_input = [self.prepare(p) for p in cast(list, run_input)]

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
        logger.debug(
            "Submitting quantum program %s to device '%s'",
            "batch" if not is_single_input else "",
            self.id,
        )
        return self.submit(run_input_compat, *args, **kwargs)

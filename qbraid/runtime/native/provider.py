# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining QbraidProvider class.

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Callable, Optional

import pyqasm
from qbraid_core.exceptions import AuthError
from qbraid_core.services.quantum import QuantumClient, QuantumServiceRequestError, process_job_data

from qbraid._caching import cached_method
from qbraid.programs import QPROGRAM_REGISTRY, ExperimentType, ProgramSpec, load_program
from qbraid.programs.typer import Qasm2StringType, Qasm3StringType
from qbraid.runtime._display import display_jobs_from_data
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.ionq.provider import IonQProvider
from qbraid.runtime.noise import NoiseModelSet
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider
from qbraid.runtime.schemas.device import DeviceData
from qbraid.transpiler import transpile

from .device import QbraidDevice

if TYPE_CHECKING:
    import pulser
    import pyqir


def _serialize_program(program) -> dict[str, str]:
    qbraid_program = load_program(program)
    return qbraid_program.serialize()


def _serialize_pyqir(program: pyqir.Module) -> dict[str, bytes]:
    return {"bitcode": program.bitcode}


def _serialize_sequence(sequence: pulser.Sequence) -> dict[str, str]:
    """Serialize a pulser sequence to a dictionary."""
    return {"sequenceBuilder": sequence.to_abstract_repr()}


def validate_qasm_no_measurements(
    program: Qasm2StringType | Qasm3StringType, device_id: str
) -> None:
    """Raises a ValueError if the given OpenQASM program contains measurement gates."""
    qasm_module = pyqasm.loads(program)

    if qasm_module.has_measurements():
        raise ValueError(
            f"OpenQASM programs submitted to the {device_id} cannot contain measurement gates."
        )


def validate_qasm_to_ionq(program: Qasm2StringType | Qasm3StringType, device_id: str) -> None:
    """Raises a ValueError if the given OpenQASM program is not compatible with IonQ JSON format."""
    try:
        transpile(program, "ionq", max_path_depth=1)
    except Exception as err:  # pylint: disable=broad-exception-caught
        raise ValueError(
            f"OpenQASM programs submitted to the {device_id} "
            "must be compatible with IonQ JSON format."
        ) from err


def get_program_spec_lambdas(
    program_type_alias: str, device_id: str
) -> dict[str, Optional[Callable[[Any], None]]]:
    """Returns conversion and validation functions for the given program type and device."""
    if program_type_alias == "pyqir":
        return {"serialize": _serialize_pyqir, "validate": None}

    if program_type_alias == "pulser":
        return {"serialize": _serialize_sequence, "validate": None}

    if program_type_alias in {"qasm2", "qasm3"}:
        device_prefix = device_id.split("_")[0]

        # pylint: disable=unnecessary-lambda-assignment
        validations = {
            "quera": lambda p: validate_qasm_no_measurements(p, device_id),
            "ionq": lambda p: validate_qasm_to_ionq(p, device_id),
        }
        # pylint: enable=unnecessary-lambda-assignment

        validate = validations.get(device_prefix)
    else:
        validate = None

    return {"serialize": _serialize_program, "validate": validate}


class QbraidProvider(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with qBraid Quantum services.

    Attributes:
        client (qbraid_core.services.quantum.QuantumClient): qBraid QuantumClient object
    """

    def __init__(self, api_key: Optional[str] = None, client: Optional[QuantumClient] = None):
        """
        Initializes the QbraidProvider object

        """
        if api_key and client:
            raise ValueError("Provide either api_key or client, not both.")

        self._api_key = api_key
        self._client = client

    def save_config(self, **kwargs):
        """Save the current configuration."""
        self.client.session.save_config(**kwargs)

    @property
    def client(self) -> QuantumClient:
        """Return the QuantumClient object."""
        if self._client is None:
            try:
                self._client = QuantumClient(api_key=self._api_key)
            except AuthError as err:
                raise ResourceNotFoundError(
                    "Failed to authenticate with the Quantum service."
                ) from err
        return self._client

    @staticmethod
    def _get_program_spec(run_package: Optional[str], device_id: str) -> Optional[ProgramSpec]:
        """Return the program spec for the given run package and device."""
        if not run_package:
            return None

        program_type = QPROGRAM_REGISTRY.get(run_package)
        if program_type is None:
            warnings.warn(
                f"The default runtime configuration for device '{device_id}' includes "
                f"transpilation to program type '{run_package}', which is not registered.",
                RuntimeWarning,
            )
        lambdas = get_program_spec_lambdas(run_package, device_id)
        return ProgramSpec(program_type, alias=run_package, **lambdas) if program_type else None

    @staticmethod
    def _get_program_specs(run_input_types: list[str], device_id: str) -> list[ProgramSpec]:
        """Return a list of program specs for the given run input types and device."""
        return [
            spec
            for rp in run_input_types
            if (spec := QbraidProvider._get_program_spec(rp, device_id)) is not None
        ]

    @staticmethod
    def _get_basis_gates(device_data: dict[str, Any]) -> Optional[list[str]]:
        """Return the basis gates for the qBraid device."""
        provider = device_data["provider"]
        if provider == "IonQ":
            ionq_id = device_data["objArg"]
            return IonQProvider._get_basis_gates(ionq_id)
        return None

    def _build_runtime_profile(self, device_data: dict[str, Any]) -> TargetProfile:
        """Builds a runtime profile from qBraid device data."""
        model = DeviceData(**device_data)
        simulator = str(model.device_type).upper() == "SIMULATOR"
        specs = self._get_program_specs(model.run_input_types, model.device_id)
        program_spec = specs[0] if len(specs) == 1 else specs or None
        noise_models = (
            NoiseModelSet.from_iterable(model.noise_models) if model.noise_models else None
        )
        device_exp_type = "gate_model" if model.paradigm == "gate-based" else model.paradigm.lower()
        experiment_type = ExperimentType(device_exp_type)
        basis_gates = self._get_basis_gates(device_data)

        return TargetProfile(
            device_id=model.device_id,
            simulator=simulator,
            experiment_type=experiment_type,
            num_qubits=model.num_qubits,
            program_spec=program_spec,
            provider_name=model.provider,
            noise_models=noise_models,
            name=model.name,
            pricing=model.pricing,
            basis_gates=basis_gates,
        )

    @cached_method(ttl=120)
    def get_devices(self, **kwargs) -> list[QbraidDevice]:
        """Return a list of devices matching the specified filtering."""
        query = kwargs or None

        try:
            devices = self.client.search_devices(query)
        except (ValueError, QuantumServiceRequestError) as err:
            raise ResourceNotFoundError("No devices found matching given criteria.") from err

        filtered_devices = [
            device
            for device in devices
            if device["vendor"] == "qBraid"
            or (
                device["vendor"] == "AWS"
                and device["provider"] in {"AWS", "QuEra", "OQC", "IQM", "Rigetti"}
            )
            or (
                device["vendor"] == "Azure"
                and device["provider"] in {"Azure", "IonQ", "Quantinuum", "Rigetti", "Pasqal"}
            )
        ]

        if not filtered_devices:
            raise ResourceNotFoundError("No devices found matching given criteria.")

        profiles = [self._build_runtime_profile(device_data) for device_data in filtered_devices]
        return [QbraidDevice(profile, client=self.client) for profile in profiles]

    @cached_method(ttl=120)
    def get_device(self, device_id: str) -> QbraidDevice:
        """Return quantum device corresponding to the specified qBraid device ID.

        Returns:
            QuantumDevice: the quantum device corresponding to the given ID

        Raises:
            ResourceNotFoundError: if device cannot be loaded from quantum service data
        """
        try:
            device_data = self.client.get_device(qbraid_id=device_id)
        except (ValueError, QuantumServiceRequestError) as err:
            raise ResourceNotFoundError(f"Device '{device_id}' not found.") from err

        profile = self._build_runtime_profile(device_data)
        return QbraidDevice(profile, client=self.client)

    # pylint: disable-next=too-many-arguments
    def display_jobs(
        self,
        device_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[dict] = None,
        max_results: int = 10,
    ):
        """Displays a list of quantum jobs submitted by user, tabulated by job ID,
        the date/time it was submitted, and status. You can specify filters to
        narrow the search by supplying a dictionary containing the desired criteria.

        Args:
            device_id (optional, str): The qBraid ID of the device used in the job.
            provider (optional, str): The name of the provider.
            tags (optional, dict): A list of tags associated with the job.
            status (optional, str): The status of the job.
            max_results (optional, int): Maximum number of results to display. Defaults to 10.
        """
        query: dict[str, Any] = {}

        if provider:
            query["provider"] = provider.lower()

        if device_id:
            query["qbraidDeviceId"] = device_id

        if status:
            query["status"] = status

        if tags:
            query.update({f"tags.{key}": value for key, value in tags.items()})

        if max_results:
            query["resultsPerPage"] = max_results

        jobs = self.client.search_jobs(query)

        job_data, msg = process_job_data(jobs, query)
        return display_jobs_from_data(job_data, msg)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            user_metadata = self.client._user_metadata
            organization_role = f'{user_metadata["organization"]}-{user_metadata["role"]}'
            hash_value = hash(
                (self.__class__.__name__, self.client.session.api_key, organization_role)
            )
            object.__setattr__(self, "_hash", hash_value)
        return self._hash  # pylint: disable=no-member

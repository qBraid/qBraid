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
Module defining QbraidProvider class.

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from qbraid_core.exceptions import AuthError
from qbraid_core.services.quantum import QuantumClient, QuantumServiceRequestError, process_job_data

from qbraid._caching import cached_method
from qbraid.passes.qasm.analyze import has_measurements
from qbraid.passes.qasm.format import format_qasm
from qbraid.programs import QPROGRAM_REGISTRY, ExperimentType, ProgramSpec, load_program
from qbraid.programs.typer import Qasm2StringType, Qasm3StringType
from qbraid.runtime._display import display_jobs_from_data
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.noise import NoiseModelSet
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider
from qbraid.runtime.schemas.device import DeviceData

from .device import QbraidDevice

if TYPE_CHECKING:
    import pyqir
    import pyqubo

    from qbraid.programs.annealing.cpp_pyqubo import PyQuboModel


def _pyqir_to_json(program: pyqir.Module) -> dict[str, bytes]:
    return {"bitcode": program.bitcode}


def _qasm_to_json(
    program: Union[Qasm2StringType, Qasm3StringType]
) -> dict[str, Union[Qasm2StringType, Qasm3StringType]]:
    return {"openQasm": format_qasm(program)}


def _pyqubo_to_json(program: pyqubo.Model) -> dict[str, dict[str, Any]]:
    program: PyQuboModel = load_program(program)
    return {"problem": program.to_json()}


def validate_qasm_no_measurements(
    program: Union[Qasm2StringType, Qasm3StringType], device_id: str
) -> None:
    """Raises a ValueError if the given OpenQASM program contains measurement gates."""
    if has_measurements(program):
        raise ValueError(
            f"OpenQASM programs submitted to the {device_id} cannot contain measurement gates."
        )


def get_program_spec_lambdas(
    program_type_alias: str, device_id: str
) -> dict[str, Optional[Callable[[Any], None]]]:
    """Returns conversion and validation functions for the given program type and device."""
    lambdas = {
        "pyqir": (_pyqir_to_json, None),
        "qasm2": (_qasm_to_json, None),
        "qasm3": (_qasm_to_json, None),
        "cpp_pyqubo": (_pyqubo_to_json, None),
    }

    to_ir, validate = lambdas.get(program_type_alias, (None, None))

    if program_type_alias in ["qasm2", "qasm3"] and device_id == "quera_qasm_simulator":
        # pylint: disable-next=unnecessary-lambda-assignment
        validate = lambda program: validate_qasm_no_measurements(program, device_id)

    return {"to_ir": to_ir, "validate": validate}


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

    def _build_runtime_profile(self, device_data: dict[str, Any]) -> TargetProfile:
        """Builds a runtime profile from qBraid device data."""
        model = DeviceData(**device_data)
        simulator = str(model.device_type).upper() == "SIMULATOR"
        program_spec = self._get_program_spec(model.run_package, model.device_id)
        noise_models = (
            NoiseModelSet.from_iterable(model.noise_models) if model.noise_models else None
        )
        device_exp_type = "gate_model" if model.paradigm == "gate-based" else model.paradigm.lower()
        experiment_type = ExperimentType(device_exp_type)
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
        )

    @cached_method(ttl=120)
    def get_devices(self, **kwargs) -> list[QbraidDevice]:
        """Return a list of devices matching the specified filtering."""
        query = kwargs or {}
        query["vendor"] = "qBraid"

        try:
            device_data_lst = self.client.search_devices(query)
        except (ValueError, QuantumServiceRequestError) as err:
            raise ResourceNotFoundError("No devices found matching given criteria.") from err

        profiles = [self._build_runtime_profile(device_data) for device_data in device_data_lst]
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

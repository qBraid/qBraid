# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module defining QbraidProvider class.

"""
from __future__ import annotations

import base64
import json
import warnings
from typing import TYPE_CHECKING, Any, Callable, Optional

import pyqasm
from qbraid_core.exceptions import AuthError
from qbraid_core.services.runtime import QuantumRuntimeClient, QuantumRuntimeServiceRequestError
from qbraid_core.services.runtime.schemas import Program, RuntimeDevice

from qbraid._caching import cached_method
from qbraid.programs import QPROGRAM_REGISTRY, ProgramSpec, load_program
from qbraid.programs.typer import Qasm2StringType, Qasm3StringType
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.ionq.provider import IonQProvider
from qbraid.runtime.noise import NoiseModelSet
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider
from qbraid.transpiler import transpile

from .device import QbraidDevice

if TYPE_CHECKING:
    import pulser
    import pyqir


def _serialize_program(program) -> Program:
    qbraid_program = load_program(program)
    return qbraid_program.serialize()


def _serialize_pyqir(program: pyqir.Module) -> Program:
    # Base64 encode the bitcode so it can be JSON-serialized for API requests
    bitcode_b64 = base64.b64encode(program.bitcode).decode("utf-8")
    return Program(
        format="qir.bc",
        data=bitcode_b64,
    )


def _serialize_sequence(sequence: pulser.Sequence) -> Program:
    """Serialize a pulser sequence to a dictionary."""
    return Program(
        format="pulser.sequence",
        data={"sequence_builder": json.loads(sequence.to_abstract_repr())},
    )


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
        client (qbraid_core.services.runtime.QuantumRuntimeClient):
            qBraid QuantumRuntimeClient object
    """

    def __init__(
        self, api_key: Optional[str] = None, client: Optional[QuantumRuntimeClient] = None
    ):
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
    def client(self) -> QuantumRuntimeClient:
        """Return the QuantumRuntimeClient object."""
        if self._client is None:
            try:
                self._client = QuantumRuntimeClient(api_key=self._api_key)
            except AuthError as err:
                raise ResourceNotFoundError(
                    "Failed to authenticate with the Quantum Runtime service."
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
    def _get_basis_gates(device_qrn: str) -> Optional[list[str]]:
        """Return the basis gates for the qBraid device."""
        _vendor, provider, device_type, name = device_qrn.split(":")
        if provider == "ionq":
            ionq_id = "simulator" if device_type == "sim" else f"qpu.{name}"
            return IonQProvider._get_basis_gates(ionq_id)
        return None

    def _build_runtime_profile(self, device: RuntimeDevice) -> TargetProfile:
        """Builds a runtime profile from qBraid device data."""
        simulator = device.deviceType == "SIMULATOR"
        specs = self._get_program_specs(device.runInputTypes, device.qrn)
        program_spec = specs[0] if len(specs) == 1 else specs or None
        noise_models = (
            NoiseModelSet.from_iterable(device.noiseModels) if device.noiseModels else None
        )
        experiment_type = device.paradigm
        basis_gates = self._get_basis_gates(device.qrn)
        provider = device.qrn.split(":")[1]

        return TargetProfile(
            device_id=device.qrn,
            simulator=simulator,
            experiment_type=experiment_type,
            num_qubits=device.numberQubits,
            program_spec=program_spec,
            provider_name=provider,
            noise_models=noise_models,
            name=device.name,
            pricing=device.pricing,
            basis_gates=basis_gates,
        )

    @cached_method(ttl=120)
    def get_devices(self) -> list[QbraidDevice]:
        """Return a list of devices matching the specified filtering."""
        # query = kwargs or None

        try:
            # TODO: Implement support for device query
            devices = self.client.list_devices()
        except (ValueError, QuantumRuntimeServiceRequestError) as err:
            raise ResourceNotFoundError("No devices found matching given criteria.") from err

        filtered_devices = [device for device in devices if device.directAccess is True]

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
            ResourceNotFoundError: If device cannot be loaded from quantum service data
            ValueError: If qBraid does not support direct access to the device
        """
        try:
            device_model = self.client.get_device(device_id)
        except (ValueError, QuantumRuntimeServiceRequestError) as err:
            raise ResourceNotFoundError(f"Device '{device_id}' not found.") from err

        if not device_model.directAccess:
            raise ValueError(
                f"qBraid does not currently support direct access to device '{device_id}'."
            )

        profile = self._build_runtime_profile(device_model)
        return QbraidDevice(profile, client=self.client)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            user_metadata = self.client._user_metadata
            organization_user_id = user_metadata["organizationUserId"]
            hash_value = hash(
                (self.__class__.__name__, self.client.session.api_key, organization_user_id)
            )
            object.__setattr__(self, "_hash", hash_value)
        return self._hash  # pylint: disable=no-member

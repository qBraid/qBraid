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
Module defining Azure Provider class for retrieving all Azure backends.

"""
from __future__ import annotations

import json
import os
import warnings
from typing import TYPE_CHECKING, Optional

from azure.identity import ClientSecretCredential
from azure.quantum import Workspace
from azure.quantum.target import Target
from qbraid_core._import import LazyLoader

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, IonQDict, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import AzureQuantumDevice
from .io_format import InputDataFormat

if TYPE_CHECKING:
    from pulser.sequence import Sequence

pyquil = LazyLoader("pyquil", globals(), "pyquil")
pyqir = LazyLoader("pyqir", globals(), "pyqir")
pulser = LazyLoader("pulser", globals(), "pulser")

DEVICE_NUM_QUBITS = {
    "ionq.simulator": 29,
    "ionq.qpu.aria-1": 25,
    "ionq.qpu.aria-2": 25,
    "ionq.qpu.forte": 32,
    "quantinuum.sim.h1-1sc": 20,
    "quantinuum.sim.h2-1sc": 56,
    "quantinuum.sim.h2-2sc": 56,
    "quantinuum.sim.h1-1e": 20,
    "quantinuum.sim.h2-1e": 32,
    "quantinuum.sim.h2-2e": 32,
    "quantinuum.qpu.h1-1": 20,
    "quantinuum.qpu.h2-1": 56,
    "quantinuum.qpu.h2-2": 56,
    "rigetti.sim.qvm": None,
    "rigetti.qpu.ankaa-3": 84,
    "pasqal.sim.emu-tn": 100,
    "pasqal.qpu.fresnel": 100,
}


def serialize_pulser_input(seq: Sequence) -> str:
    """Convert a Pulser sequence to a JSON string."""
    input_data = {}
    input_data["sequence_builder"] = json.loads(seq.to_abstract_repr())
    to_send = json.dumps(input_data)
    return to_send


class AzureQuantumProvider(QuantumProvider):
    """
    Manages interactions with Azure Quantum services, encapsulating API calls,
    handling Azure Storage, and managing sessions.

    Attributes:
        workspace (Workspace): The configured Azure Quantum workspace.
    """

    def __init__(
        self,
        workspace: Optional[Workspace] = None,
        credential: Optional[ClientSecretCredential] = None,
    ):
        """
        Initializes an AzureQuantumProvider instance with a specified Workspace. It sets the
        credential for the workspace if it is not already set and a credential is provided.

        Args:
            workspace (Workspace, optional): An Azure Quantum Workspace object. If not provided,
                will be initialized with the provided credential or from environment variables.
            credential (ClientSecretCredential, optional): Optional credential to be used
                if the workspace lacks one.
        """
        if not workspace:
            connection_str = os.getenv("AZURE_QUANTUM_CONNECTION_STRING")
            workspace = (
                Workspace.from_connection_string(connection_str) if connection_str else Workspace()
            )

        if not workspace.credential:
            if credential:
                workspace.credential = credential
            else:
                warnings.warn(
                    "No credential provided; interactive authentication via a "
                    "web browser may be required. To avoid interactive authentication, "
                    "provide a ClientSecretCredential."
                )
        workspace.append_user_agent("qbraid")
        self._workspace = workspace

    @property
    def workspace(self) -> Workspace:
        """Get the Azure Quantum workspace."""
        return self._workspace

    @staticmethod
    def _get_program_spec(input_data_format: InputDataFormat) -> Optional[ProgramSpec]:
        """Get the program specification based on the input data format."""
        try:
            if input_data_format == InputDataFormat.MICROSOFT:
                return ProgramSpec(
                    pyqir.Module, alias="pyqir", serialize=lambda module: module.bitcode
                )
            if input_data_format == InputDataFormat.IONQ:
                return ProgramSpec(IonQDict, alias="ionq", serialize=lambda ionq_dict: ionq_dict)
            if input_data_format == InputDataFormat.QUANTINUUM:
                return ProgramSpec(str, alias="qasm2", serialize=lambda qasm: qasm)
            if input_data_format == InputDataFormat.RIGETTI:
                return ProgramSpec(
                    pyquil.Program, alias="pyquil", serialize=lambda program: program.out()
                )
            if input_data_format == InputDataFormat.PASQAL:
                return ProgramSpec(
                    pulser.sequence.Sequence, alias="pulser", serialize=serialize_pulser_input
                )
        except ModuleNotFoundError as err:  # pragma: no cover
            warnings.warn(
                f"The default runtime configuration for device using input data format "
                f"'{input_data_format.value}' requires package '{err.name}', "
                "which is not installed.",
                RuntimeWarning,
            )

        return None  # pragma: no cover

    @staticmethod
    def _get_experiment_type(input_data_format: InputDataFormat) -> ExperimentType:
        """Get the experiment type based on the input data format."""
        if input_data_format == InputDataFormat.PASQAL:
            return ExperimentType.AHS
        return ExperimentType.GATE_MODEL

    def _build_profile(self, target: Target) -> TargetProfile:
        """Builds a profile for an Azure device.

        Args:
            target (Target): The Target object to build profile from.

        Returns:
            TargetProfile: The completed profile.
        """
        device_id = target.name
        provider_name = target.provider_id
        simulator = device_id.split(".", 2)[1] != "qpu"
        capability = target.capability
        input_data_format = target.input_data_format
        output_data_format = target.output_data_format
        content_type = target.content_type

        num_qubits = DEVICE_NUM_QUBITS.get(device_id)

        try:
            input_data_format_enum = InputDataFormat(input_data_format)
        except ValueError:
            warnings.warn(f"Unrecognized input data format: {input_data_format}")
            experiment_type = None
            program_spec = None
        else:
            experiment_type = self._get_experiment_type(input_data_format_enum)
            program_spec = self._get_program_spec(input_data_format_enum)

        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            provider_name=provider_name,
            num_qubits=num_qubits,
            capability=capability,
            input_data_format=input_data_format,
            output_data_format=output_data_format,
            content_type=content_type,
            experiment_type=experiment_type,
            program_spec=program_spec,
        )

    @cached_method
    def get_devices(self, **kwargs) -> list[AzureQuantumDevice]:
        """Get all Azure Quantum devices.

        Args:
            **kwargs: Filters for the devices to retrieve.

        Returns:
            list[AzureQuantumDevice]: The Azure Quantum devices.

        """
        targets = self.workspace.get_targets(**kwargs)
        if isinstance(targets, Target):
            targets = [targets]

        if len(targets) == 0:
            if len(kwargs) > 0:
                raise ValueError("No devices found with the specified filters.")
            raise ResourceNotFoundError("No devices found.")

        return [
            AzureQuantumDevice(self._build_profile(target), self.workspace) for target in targets
        ]

    @cached_method
    def get_device(self, device_id: str) -> AzureQuantumDevice:
        """Get a specific Azure Quantum device.

        Args:
            device_id (str): The ID of the device to retrieve.

        Returns:
            AzureQuantumDevice: The Azure Quantum device.

        """
        target = self.workspace.get_targets(name=device_id)
        if not target:
            raise ValueError(f"Device {device_id} not found.")
        return AzureQuantumDevice(self._build_profile(target), self.workspace)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(
                self, "_hash", hash((self._workspace.credential, self._workspace.user_agent))
            )
        return self._hash  # pylint: disable=no-member

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
Module defining Azure Provider class for retrieving all Azure backends.

"""
import warnings
from typing import Optional

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

pyquil = LazyLoader("pyquil", globals(), "pyquil")
pyqir = LazyLoader("pyqir", globals(), "pyqir")


class AzureQuantumProvider(QuantumProvider):
    """
    Manages interactions with Azure Quantum services, encapsulating API calls,
    handling Azure Storage, and managing sessions.

    Attributes:
        workspace (Workspace): The configured Azure Quantum workspace.
    """

    def __init__(self, workspace: Workspace, credential: Optional[ClientSecretCredential] = None):
        """
        Initializes an AzureQuantumProvider instance with a specified Workspace. It sets the
        credential for the workspace if it is not already set and a credential is provided.

        Args:
            workspace (Workspace): An initialized Azure Quantum Workspace object.
            credential (Optional[ClientSecretCredential]): Optional credential to be used
                if the workspace lacks one.
        """
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

    def _build_profile(self, target: Target) -> TargetProfile:
        """Builds a profile for an Azure device.

        Args:
            target (Target): The Target object to build profile from.

        Returns:
            TargetProfile: The completed profile.
        """
        device_id = target.name
        provider_name = target.provider_id
        simulator = device_id.split(".", 1)[1] != "qpu"
        capability = target.capability
        input_data_format = target.input_data_format
        output_data_format = target.output_data_format
        content_type = target.content_type

        if input_data_format == InputDataFormat.MICROSOFT.value:
            program_spec = ProgramSpec(
                pyqir.Module, alias="pyqir", to_ir=lambda module: module.bitcode
            )
        elif input_data_format == InputDataFormat.IONQ.value:
            program_spec = ProgramSpec(IonQDict, alias="ionq", to_ir=lambda ionq_dict: ionq_dict)
        elif input_data_format == InputDataFormat.QUANTINUUM.value:
            program_spec = ProgramSpec(str, alias="qasm2", to_ir=lambda qasm: qasm)
        elif input_data_format == InputDataFormat.RIGETTI.value:
            program_spec = ProgramSpec(
                pyquil.Program, alias="pyquil", to_ir=lambda program: program.out()
            )
        else:
            program_spec = None
            warnings.warn(f"Unrecognized input data format: {input_data_format}")

        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            provider_name=provider_name,
            capability=capability,
            input_data_format=input_data_format,
            output_data_format=output_data_format,
            content_type=content_type,
            experiment_type=ExperimentType.GATE_MODEL,
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

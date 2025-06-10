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
Module defining Rigettu provider class

"""

import os

from pyquil.api import QCSClient, get_qc
from qcs_sdk.client import AuthServer, OAuthSession, RefreshToken
from qcs_sdk.qpu import list_quantum_processors
from qcs_sdk.qpu.isa import get_instruction_set_architecture

from qbraid.programs.experiment import ExperimentType
from qbraid.programs.spec import ProgramSpec
from qbraid.runtime import QuantumDevice, QuantumProvider, TargetProfile

from .device import RigettiDevice


class RigettiProvider(QuantumProvider):
    """
    Implements qBraid’s QuantumProvider interface for Rigetti QCS.
    """

    def __init__(
        self,
        qcs_client: QCSClient = None,
        as_qvm: bool = True,
    ):
        self._qcs_client = qcs_client
        if self._qcs_client is not None:
            self.refresh_token = os.getenv("RIGETTI_REFRESH_TOKEN")
            if not self.refresh_token:
                raise ValueError(
                    "A Rigetti access token is required."
                    " Set it via RIGETTI_REFRESH_TOKEN or pass directly."
                )
            self.client_id = os.getenv("RIGETTI_CLIENT_ID")
            if not self.client_id:
                raise ValueError(
                    "A Rigetti client ID is required."
                    " Set it via RIGETTI_CLIENT_ID or pass directly."
                )
            self.issuer = os.getenv("RIGETTI_ISSUER")
            if not self.issuer:
                raise ValueError(
                    "A Rigetti issuer is required. Set it via RIGETTI_ISSUER or pass directly."
                )
            self.qcs_client = QCSClient(
                oauth_session=OAuthSession(
                    RefreshToken(
                        refresh_token=os.getenv("RIGETTI_REFRESH_TOKEN"),
                    ),
                    AuthServer(
                        client_id=os.getenv("RIGETTI_CLIENT_ID"),
                        issuer=os.getenv("RIGETTI_ISSUER"),
                    ),
                ),
            )
        self._as_qvm = as_qvm

    def _build_profile(self, quantum_processor_id: str) -> TargetProfile:
        if not self._as_qvm:
            instruction_set_architecture = get_instruction_set_architecture(
                quantum_processor_id=quantum_processor_id,
                client=self._qcs_client,
            )
            device_id = instruction_set_architecture.name
            num_qubits = len(instruction_set_architecture.architecture.nodes)
        else:
            qc = get_qc(
                name=quantum_processor_id,
                as_qvm=self._as_qvm,
            )
            device_id = quantum_processor_id
            num_qubits = len(qc.qubits())
        return TargetProfile(
            device_id=device_id,
            simulator=self._as_qvm,
            experiment_type=ExperimentType.GATE_MODEL,
            program_spec=ProgramSpec(str, alias="qasm3"),
            num_qubits=num_qubits,
            provider_name="rigetti",
        )

    def get_devices(self) -> list[RigettiDevice]:
        devices: list[QuantumDevice] = []
        quantum_processor_ids = list_quantum_processors(client=self._qcs_client)
        for quantum_processor_id in quantum_processor_ids:
            profile = self._build_profile(quantum_processor_id=quantum_processor_id)
            devices.append(RigettiDevice(profile=profile, qcs_client=self._qcs_client))

        return devices

    def get_device(self, device_id: str) -> RigettiDevice:
        profile = self._build_profile(quantum_processor_id=device_id)
        return RigettiDevice(profile=profile, qcs_client=self._qcs_client)

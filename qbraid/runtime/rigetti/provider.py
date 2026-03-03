# Copyright 2026 qBraid
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
Module defining Rigetti provider class

"""

import os

import pyquil
from qcs_sdk.client import AuthServer, OAuthSession, QCSClient, RefreshToken
from qcs_sdk.qpu import list_quantum_processors
from qcs_sdk.qpu.isa import get_instruction_set_architecture

from qbraid.programs.experiment import ExperimentType
from qbraid.programs.spec import ProgramSpec
from qbraid.runtime import QuantumProvider, TargetProfile

from .device import RigettiDevice


class RigettiProvider(QuantumProvider):
    """
    Implements qBraid’s QuantumProvider interface for Rigetti QCS.
    """

    def __init__(
        self,
        qcs_client: QCSClient = None,
    ):
        self._qcs_client = qcs_client
        if self._qcs_client is None:
            refresh_token = os.getenv("RIGETTI_REFRESH_TOKEN")
            if not refresh_token:
                raise ValueError(
                    "A Rigetti refresh token is required."
                    " Set it via RIGETTI_REFRESH_TOKEN or pass a QCSClient directly."
                )
            client_id = os.getenv("RIGETTI_CLIENT_ID")
            issuer = os.getenv("RIGETTI_ISSUER")
            if client_id and issuer:
                auth_server = AuthServer(client_id=client_id, issuer=issuer)
            else:
                auth_server = AuthServer.default()
            self._qcs_client = QCSClient(
                oauth_session=OAuthSession(
                    RefreshToken(refresh_token=refresh_token),
                    auth_server,
                ),
            )

    def _build_profile(self, quantum_processor_id: str) -> TargetProfile:
        instruction_set_architecture = get_instruction_set_architecture(
            quantum_processor_id=quantum_processor_id,
            client=self._qcs_client,
        )
        num_qubits = len(instruction_set_architecture.architecture.nodes)
        return TargetProfile(
            device_id=quantum_processor_id,
            simulator=False,
            experiment_type=ExperimentType.GATE_MODEL,
            program_spec=ProgramSpec(pyquil.Program),
            num_qubits=num_qubits,
            provider_name="rigetti",
        )

    def get_devices(self) -> list[RigettiDevice]:
        devices: list[RigettiDevice] = []
        quantum_processor_ids = list_quantum_processors(client=self._qcs_client)
        for qpu_id in quantum_processor_ids:
            profile = self._build_profile(quantum_processor_id=qpu_id)
            devices.append(RigettiDevice(profile=profile, qcs_client=self._qcs_client))
        return devices

    def get_device(self, device_id: str) -> RigettiDevice:
        profile = self._build_profile(quantum_processor_id=device_id)
        return RigettiDevice(profile=profile, qcs_client=self._qcs_client)

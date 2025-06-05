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

import httpx
import pyquil
import pyquil.api
from pyquil import get_qc
from qcs_api_client.operations.sync import (
    get_instruction_set_architecture,
    list_quantum_processors,
)

from qbraid.runtime import (
    QuantumDevice,
    QuantumProvider,
    TargetProfile,
)
from qbraid.runtime.exceptions import ResourceNotFoundError

from .device import RigettiDevice


class RigettiProvider(QuantumProvider):
    """
    Implements qBraid’s QuantumProvider interface for Rigetti QCS.
    """

    def __init__(
        self,
        access_token: str,
        as_qvm: bool = True,
    ):
        self.access_token = access_token or os.getenv("RIGETTI_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError(
                "A Rigetti access token is required."
                " Set it via RIGETTI_ACCESS_TOKEN or pass directly."
            )

        self._client = httpx.Client(
            base_url="https://api.qcs.rigetti.com",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            },
        )
        self._as_qvm = as_qvm

    def _is_qpu_available(self, quantum_processor_id: str) -> bool:
        """
        Return the number of qubits for a given QPU if available, else None.
        """
        data = get_instruction_set_architecture(
            quantum_processor_id=quantum_processor_id, client=self._client
        )
        if data and data.parsed:
            if hasattr(data.parsed, "architecture"):
                return True
        return False

    def _build_profile(self, provider_name: str, qc: pyquil.api.QuantumComputer) -> TargetProfile:
        return TargetProfile(
            provider_name=provider_name,
            device_id=qc.name,
            simulator=self._as_qvm,
            num_qubits=len(qc.qubits()),
        )

    def get_qc(self, name: str) -> pyquil.api.QuantumComputer:
        """
        Get a Rigetti QuantumComputer instance by name.
        If as_qvm is True, it returns a QVM instance; otherwise, it returns a QPU instance.
        """
        return get_qc(name, as_qvm=self._as_qvm)

    def get_devices(self) -> list[RigettiDevice]:
        devices: list[QuantumDevice] = []
        response = list_quantum_processors(client=self._client)
        qpu_ids = [qp.id for qp in response.parsed.quantum_processors]

        for qpu_id in qpu_ids:
            qc = self.get_qc(name=qpu_id)
            profile = self._build_profile("rigetti", qc=qc)
            devices.append(RigettiDevice(profile=profile, qc=qc))

        return devices

    def get_device(self, device_id: str) -> RigettiDevice:
        if not self._is_qpu_available(device_id):
            raise ResourceNotFoundError(f"Device {device_id} is not available.")

        qc = self.get_qc(name=device_id)
        profile = self._build_profile("rigetti", qc=qc)
        return RigettiDevice(profile=profile, qc=qc)

import os
from typing import List

import httpx
from pyquil import get_qc
from qbraid.runtime import (
    QuantumProvider,
    QuantumDevice,
    TargetProfile,
)
from qcs_api_client.operations.sync import (
    list_quantum_processors,
    get_instruction_set_architecture,
)
import pyquil
import pyquil.api

from qbraid.runtime.exceptions import ResourceNotFoundError
from .device import RigettiDevice


class RigettiProvider(QuantumProvider):
    """
    Implements qBraid’s QuantumProvider interface for Rigetti QCS.
    """

    def __init__(
        self,
        access_token: str,
    ):
        self.access_token = access_token or os.getenv("RIGETTI_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError(
                "A Rigetti access token is required. Set it via RIGETTI_ACCESS_TOKEN or pass directly."
            )

        self._client = httpx.Client(
            base_url="https://api.qcs.rigetti.com",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            },
        )

    def _is_qpu_available(self, quantum_processor_id: str) -> bool:
        """
        Return the number of qubits for a given QPU if available, else None.
        """
        try:
            data = get_instruction_set_architecture(
                quantum_processor_id=quantum_processor_id, client=self._client
            )
            if data and data.parsed and data.parsed.architecture is not None:
                return True
        except Exception:
            return False

    def _build_profile(self, provider_name: str, device_id: str, simulator: bool) -> TargetProfile:
        return TargetProfile(
            provider_name=provider_name,
            device_id=device_id,
            simulator=simulator,
        )

    def _is_simulator(self, qc: pyquil.api.QuantumComputer) -> bool:
        """
        Check if the given QuantumComputer instance is a simulator.
        """
        return not isinstance(qc.qam, pyquil.api.QPU)

    def get_devices(self, **kwargs) -> List[QuantumDevice]:
        devices: List[QuantumDevice] = []
        response = list_quantum_processors(client=self._client)
        qpu_ids = [qp.id for qp in response.parsed.quantum_processors]

        for qpu_id in qpu_ids:
            if not self._is_qpu_available(qpu_id):
                continue

            qc = get_qc(name=qpu_id)
            profile = self._build_profile("rigetti", qpu_id, simulator=self._is_simulator(qc))
            devices.append(RigettiDevice(profile=profile, qc=qc))

        return devices

    def get_device(self, device_id: str) -> QuantumDevice:
        if not self._is_qpu_available(device_id):
            raise ResourceNotFoundError(f"Device {device_id} is not available.")

        qc = get_qc(name=device_id)
        profile = self._build_profile("rigetti", device_id, simulator=self._is_simulator(qc))
        return RigettiDevice(profile=profile, qc=qc)

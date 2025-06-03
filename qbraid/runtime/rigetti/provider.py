from typing import Any, Dict, List, Optional

import httpx

from qbraid.runtime import (
    QuantumProvider,
    QuantumDevice,
    TargetProfile,
)
from qcs_api_client.client.client import _build_client_kwargs, QCSClientConfiguration
from qcs_api_client.operations.sync import (
    list_quantum_processors,
    get_instruction_set_architecture,
)
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

    def _get_qubit_count(self, quantum_processor_id: str) -> Optional[int]:
        """
        Return the number of qubits for a given QPU if available, else None.
        """
        try:
            data = get_instruction_set_architecture(
                quantum_processor_id=quantum_processor_id,
                client=self._client
            )
            if data and data.parsed and data.parsed.architecture:
                return len(data.parsed.architecture.nodes)
        except Exception:
            pass
        return None

    
    def _build_profile(self,provider_name: str, device_id: str, num_qubits: int) -> TargetProfile:
        return TargetProfile(
            provider_name=provider_name,
            device_id=device_id,
            simulator=False,
            num_qubits=num_qubits,
        )


    def get_devices(self, **kwargs) -> List[QuantumDevice]:
        devices: List[QuantumDevice] = []
        response = list_quantum_processors(client=self._client)
        qpu_ids = [qp.id for qp in response.parsed.quantum_processors]

        for qpu_id in qpu_ids:
            qubit_count = self._get_qubit_count(qpu_id)
            if qubit_count is None:
                continue

            profile = self._build_profile("rigetti", qpu_id, qubit_count)
            devices.append(RigettiDevice(profile=profile, provider_client=self._client))

        return devices

    def get_device(self, device_id: str) -> QuantumDevice:
        qubit_count = self._get_qubit_count(device_id)
        if qubit_count is None:
            raise Exception(f"Device {device_id} is not available.")

        profile = self._build_profile("rigetti", device_id, qubit_count)
        return RigettiDevice(profile=profile, provider_client=self._client)

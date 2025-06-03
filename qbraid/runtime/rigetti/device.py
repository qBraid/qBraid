from typing import Any, Dict, List, Optional

from qbraid.runtime import (
    QuantumDevice,
    QuantumJob,
    TargetProfile,
    RuntimeOptions,
)
from qcs_api_client.operations.sync import (
    get_quantum_processor,
    find_available_reservations,
    create_reservation,
)


class RigettiDevice(QuantumDevice):
    """
    Wraps a single Rigetti QCS quantum processor or simulator.
    """

    def __init__(self, profile: TargetProfile, provider_client: Any):
        """
        profile: A TargetProfile object (constructed by RigettiProvider).
        provider_client: The QCS client built via build_sync_client().
        """
        # Call base class initializer, passing the TargetProfile
        super().__init__(profile=profile, scheme=None, options=RuntimeOptions())
        self._client = provider_client
        self._device_id = profile.device_id

    @property
    def id(self) -> str:
        return self._device_id

    @property
    def num_qubits(self) -> int:
        return self.profile.num_qubits

    def metadata(self) -> Dict[str, Any]:
        """
        Return a dictionary of metadata for this device (e.g., num_qubits, status, etc.).
        """
        return {
            "device_id": self._device_id,
            "num_qubits": self.num_qubits,
            "status": self.status(),
        }

    def status(self) -> str:
        """
        Return the current status of the device.
        This is a placeholder; actual implementation may vary based on QCS API.
        """
        # For now, we assume the device is always available
        return "online"

    def submit(self, run_input, *args, **kwargs):
        pass
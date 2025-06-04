from typing import Any, Dict, List, Optional

from qbraid.runtime import (
    QuantumDevice,
    QuantumJob,
    TargetProfile,
    RuntimeOptions,
)
from pyquil import get_qc
from pyquil.api import QuantumComputer

from qbraid.runtime.enums import DeviceStatus

class RigettiDevice(QuantumDevice):
    """
    Wraps a single Rigetti QCS quantum processor or simulator.
    """

    def __init__(
        self,
        profile: TargetProfile,
        qc: QuantumComputer,
    ):
        """
        profile: A TargetProfile object (constructed by RigettiProvider).
        """
        # Call base class initializer, passing the TargetProfile
        super().__init__(profile=profile, scheme=None, options=RuntimeOptions())
        self._qc = qc
        

    @property
    def id(self) -> str:
        return self.profile.device_id

    @property
    def num_qubits(self) -> int:
        return len(self._qc.qubits())

    def metadata(self) -> Dict[str, Any]:
        """
        Return a dictionary of metadata for this device (e.g., num_qubits, status, etc.).
        """
        return {
            "device_id": self.id,
            "num_qubits": self.num_qubits,
            "status": self.status(),
        }

    def status(self) -> DeviceStatus:
        """
        Return the current status of the device.
        This is a placeholder; actual implementation may vary based on QCS API.
        """
        # For now, we assume the device is always available
        if self._qc.qubits():
            return DeviceStatus.ONLINE
        return DeviceStatus.OFFLINE

    def submit(self, run_input, *args, **kwargs):
        pass
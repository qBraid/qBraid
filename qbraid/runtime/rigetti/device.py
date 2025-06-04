from typing import Any, Dict


from qbraid.runtime import (
    QuantumDevice,
    TargetProfile,
    RuntimeOptions,
)
import pyquil
import pyquil.api

from qbraid.runtime.enums import DeviceStatus

class RigettiDevice(QuantumDevice):
    """
    Wraps a single Rigetti QCS quantum processor or simulator.
    """

    def __init__(
        self,
        profile: TargetProfile,
        qc: pyquil.api.QuantumComputer,
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

    def submit(self, run_input: pyquil.Program, *args, **kwargs):
        compiled_program = self._qc.compile(run_input)
        return self._qc.qam.execute(compiled_program, *args, **kwargs)

from abc import ABC
from ..device import Device
import cirq


def _get_google_device(device):

    if isinstance(device, cirq.Simulator):
        return GoogleSimulatorDevice(device)
    else:
        raise NotImplementedError


class GoogleSimulatorDevice(Device, ABC):
    def __init__(self, device):

        super().__init__()
        self._name = "cirq Simulator"
        self._vendor = "Google"
        self.device = device

    def validate_circuit(self):
        """Checks if a qbraid circuit can be run on this device"""
        raise NotImplementedError

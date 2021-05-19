from abc import ABC

from ..device import Device

from qiskit import Aer
from qiskit.providers import BaseBackend as QiskitBaseBackend
from qiskit.providers.backend import Backend as QiskitBackend

AerDevices = ("statevector_simulator", "qasm_simulator")
IBMQDevices = "test_device"

IBMDeviceInput = (str, QiskitBaseBackend, QiskitBackend)


def _get_ibm_device(device: IBMDeviceInput):

    if isinstance(device, (QiskitBaseBackend, QiskitBackend)):
        return IBMDevice(device)
    elif isinstance(device, str):
        if device in AerDevices:
            return IBMAerDevice(Aer.get_backend(device))
        elif device in IBMQDevices:
            raise NotImplementedError
        else:
            raise TypeError("This IBM device type is not supported.")
    else:
        raise TypeError("This IBM device type is not supported.")


class IBMDevice(Device, ABC):
    def __init__(self, backend):

        super().__init__()
        self._name = backend.name()
        self._vendor = "IBM"

    @property
    def backend(self):
        """Does the same as self.device(), returns underlying object"""
        return self.device


class IBMAerDevice(IBMDevice, ABC):
    def __init__(self, backend):

        super().__init__(backend)
        self._device = backend

    @property
    def device(self):
        return self._device

    def validate_circuit(self):
        raise NotImplementedError


class IBMQDevice(IBMDevice, ABC):
    def __init__(self, backend):

        super().__init__(backend)
        raise NotImplementedError

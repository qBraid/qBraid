from abc import ABC, abstractmethod
from qbraid.devices.exceptions import DeviceError


class QbraidDeviceWrapper(ABC):

    @property
    @abstractmethod
    def name(self):
        pass

    def _get_device_obj(self, supported_devices: dict):
        try:
            device_obj = supported_devices[self.name]
        except KeyError:
            raise DeviceError("{} is not a supported device".format(self.name))
        return device_obj

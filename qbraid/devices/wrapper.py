from abc import ABC, abstractmethod
from qbraid.devices.exceptions import DeviceError


class QbraidDeviceWrapper(ABC):

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def provider(self):
        pass

    @property
    @abstractmethod
    def vendor(self):
        pass

    def _get_device_obj(self, supported_providers: dict):
        try:
            supported_devices = supported_providers[self.provider]
        except KeyError:
            raise DeviceError(
                "Provider \"{}\" not supported by vendor \"{}\".".format(self.provider, self.vendor)
            )
        try:
            device_object = supported_devices[self.name]
        except KeyError:
            msg = "Device \"{}\" not supported by provider \"{}\"".format(self.name, self.provider)
            if self.provider != self.vendor:
                msg += " from vendor \"{}\"".format(self.vendor)
            raise DeviceError(msg + ".")
        return device_object

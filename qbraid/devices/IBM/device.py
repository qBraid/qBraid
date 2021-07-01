from ..device import DeviceWrapper
from .utils import SUPPORTED_DEVICES


class IBMDeviceWrapper(DeviceWrapper):

    def __init__(self, name, provider, **fields):
        """AWS device wrapper class
        Args:
            name (str): a qBraid supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.
        Raises:
            AttributeError: if input field not a valid options
        """
        super().__init__(name, provider, **fields)
        self._device_obj = self._get_device_obj(SUPPORTED_DEVICES)

    @classmethod
    def _default_options(cls):
        """Return the default options
        This method will return a :class:`qiskit.providers.Options`
        subclass object that will be used for the default options. These
        should be the default parameters to use for the options of the
        backend.
        Returns:
            qiskit.providers.Options: A options object with default values set
        """
        pass

    def run(self, run_input, **options):
        pass

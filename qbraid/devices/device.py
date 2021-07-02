"""Device abstract interface."""

from abc import abstractmethod
from .wrapper import QbraidDeviceWrapper


class DeviceWrapper(QbraidDeviceWrapper):

    def __init__(self, name, provider, **fields):
        """Initialize a device class
        Args:
            name (str): a qBraid supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.
        Raises:
            AttributeError: if input field not a valid options
        """
        self._name = name
        self._provider = provider
        self._options = self._default_options()
        self._configuration = None
        self.root_device_obj = None
        if fields:
            for field in fields:
                if field not in self._options.data:
                    raise AttributeError("Options field %s is not valid for this device" % field)
            self._options.update_config(**fields)

    @classmethod
    @abstractmethod
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

    def set_options(self, **fields):
        """Set the options fields for the device.
        This method is used to update the options of a device. If
        you need to change any of the options prior to running just
        pass in the kwarg with the new value for the options.
        Args:
            fields: The fields to update the options
        Raises:
            AttributeError: If the field passed in is not part of the options
        """
        for field in fields:
            if not hasattr(self._options, field):
                raise AttributeError("Options field %s is not valid for this " "device" % field)
        self._options.update_options(**fields)

    def configuration(self):
        """Return the device configuration.
        Returns:
            dict: the configuration for the device. If the device does not support properties,
            it returns ``None``.
        """
        return self._configuration

    @property
    def name(self):
        """Return the device name.
        Returns:
            str: the name of the device.
        """
        return self._name

    @property
    def provider(self):
        """Return the device provider.
        Returns:
            str: the provider responsible for the device.
        """
        return self._provider

    @property
    def options(self):
        """Return the options for the device
        The options of a device are the dynamic parameters defining
        how the device is used. These are used to control the :meth:`run`
        method.
        """
        return self._options

    def __str__(self):
        return self.name

    def __repr__(self):
        """Official string representation of a Backend.
        Note that, by Qiskit convention, it is consciously *not* a fully valid
        Python expression. Subclasses should provide 'a string of the form
        <...some useful description...>'. [0]
        [0] https://docs.python.org/3/reference/datamodel.html#object.__repr__
        """
        return f"<{self.__class__.__name__}('{self.name}')>"

    @abstractmethod
    def run(self, run_input, **options):
        pass

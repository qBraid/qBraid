# This code is part of Qiskit.
#
# (C) Copyright IBM 2017.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of the source tree https://github.com/Qiskit/qiskit-terra/blob/main/LICENSE.txt
# or at http://www.apache.org/licenses/LICENSE-2.0.
#
# NOTICE: This file has been modified from the original:
# https://github.com/Qiskit/qiskit-terra/blob/main/qiskit/providers/backend.py

from abc import abstractmethod
from .wrapper import QbraidDeviceLikeWrapper


class DeviceLikeWrapper(QbraidDeviceLikeWrapper):
    def __init__(self, name, provider, **fields):
        """Abstract interface for device-like classes.
        Args:
            name (str): a qBraid supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.
        Raises:
            AttributeError: if input field not a valid options
        """
        self._name = name
        self._provider = provider
        self._vendor = None
        self._options = self._default_options()
        self._configuration = None
        self.vendor_dlo = None  # vendor device-like object
        if fields:
            for field in fields:
                if field not in self._options.data:
                    raise AttributeError("Options field %s is not valid for this device" % field)
            self._options.update_config(**fields)

    @classmethod
    @abstractmethod
    def _default_options(cls):
        """Return the default options for running this device."""
        pass

    def set_options(self, **fields):
        """Set the options fields for the device.
        This method is used to update the options of a device. If you need to change any of the
        options prior to running just pass in the kwarg with the new value for the options.
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
    def vendor(self):
        """Return the software vendor name.
        Returns:
            str: the name of the software vendor.
        """
        return self._vendor

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
        """String representation of a DeviceWrapper object."""
        return f"<{self.__class__.__name__}({self.provider}:'{self.name}')>"

    @abstractmethod
    def run(self, run_input, **options):
        pass

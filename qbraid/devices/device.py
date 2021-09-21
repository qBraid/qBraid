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

"""DeviceLikeWrapper Class"""

from abc import ABC, abstractmethod

import qbraid
from qbraid.devices._utils import (
    CONFIG_PROMPTS,
    RUN_PACKAGE,
    SUPPORTED_DEVICES,
    get_config,
    set_config,
)
from qbraid.devices.exceptions import DeviceError


class DeviceLikeWrapper(ABC):
    """Abstract interface for device-like classes.

    Args:
        name (str): a qBraid supported device
        provider (str): the provider that this device comes from
        fields: kwargs for the values to use to override the default options.

    Raises:
        DeviceError: if input field not a valid options

    """

    def __init__(self, device_id, provider, vendor=None, **fields):

        self._name = device_id
        self._provider = provider
        self._vendor = vendor
        self._options = self._default_options()
        self._device_configuration = None
        self._run_package = RUN_PACKAGE[self.vendor]
        self.requires_creds = False
        self.vendor_dlo = self._get_device_obj()  # vendor device-like object
        if fields:
            for field in fields:
                if field not in self._options.data:
                    raise DeviceError(f"Options field {field} is not valid for this device")
            self._options.update_config(**fields)

    def _get_device_obj(self):
        try:
            supported_devices = SUPPORTED_DEVICES[self.vendor]
        except KeyError as err:
            raise DeviceError(
                '"{}" is not a supported by vendor.'.format(self.vendor)
            ) from err
        try:
            device_ref = supported_devices[self.name]
        except KeyError as err:
            msg = 'Device "{}" not supported by provider "{}"'.format(self.name, self.provider)
            if self.provider != self.vendor:
                msg += ' from vendor "{}"'.format(self.vendor)
            raise DeviceError(msg + ".") from err
        if device_ref is None:
            raise DeviceError("Device not currently available.")
        if isinstance(device_ref, str):
            if get_config("verify", self.vendor) != "True":
                prompt_lst = CONFIG_PROMPTS[self.vendor]
                for prompt in prompt_lst:
                    set_config(*prompt)
            self.requires_creds = True
            return self._init_cred_device(device_ref)
        return device_ref

    def _compat_run_input(self, run_input):
        """Checks if ``run_input`` is compatible with device and if not, calls transpiler."""
        run_input_package = run_input.__module__.split(".")[0]
        if run_input_package != self._run_package:
            run_input = qbraid.circuit_wrapper(run_input).transpile(self._run_package)
        return run_input

    @abstractmethod
    def _init_cred_device(self, device_ref):
        """Returns device object associated with given device_ref. This method is invoked when
         a user has called the qBraid device wrapper on a device that requires a particular set
         of credentials to access, e.g. an AWS, Google Cloud, or IBMQ account.

        Args:
            device_ref (str): string representation of device.

        Raises:
            ConfigError when device_rep is invalid

        """

    @classmethod
    @abstractmethod
    def _default_options(cls):
        """Return the default options for running this device."""

    def set_options(self, **fields):
        """Set the options fields for the device.

        This method is used to update the options of a device. If you need to change any of the
        options prior to running just pass in the kwarg with the new value for the options.

        Args:
            fields: The fields to update the options

        Raises:
            DeviceError: If the field passed in is not part of the options

        """
        for field in fields:
            if not hasattr(self._options, field):
                raise DeviceError(f"Options field {field} is not valid for this device.")
        self._options.update_options(**fields)

    def device_configuration(self):
        """Return the device configuration.

        Returns:
            dict: the configuration for the device. If the device does not support properties,
            it returns ``None``.

        """
        return self._device_configuration

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
        if self._vendor is None:
            raise DeviceError("vendor is None")
        return self._vendor

    @property
    def options(self):
        """Return the options for the device.

        The options of a device are the dynamic parameters defining
        how the device is used. These are used to control the :meth:`run`
        method.

        """
        return self._options

    def __str__(self):
        return f"{self.vendor} {self.provider} {self.name} device wrapper"

    def __repr__(self):
        """String representation of a DeviceWrapper object."""
        return f"<{self.__class__.__name__}({self.provider}:'{self.name}')>"

    @abstractmethod
    def run(self, run_input, *args, **kwargs):
        """Abstract run method."""

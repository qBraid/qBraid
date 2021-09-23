"""DeviceLikeWrapper Class"""

from abc import ABC, abstractmethod

import qbraid
from qbraid.devices._utils import (
    CONFIG_PROMPTS,
    get_config,
    set_config,
)


class DeviceLikeWrapper(ABC):
    """Abstract interface for device-like classes.

    Args:
        name (str): a qBraid supported device
        provider (str): the provider that this device comes from
        fields: kwargs for the values to use to override the default options.

    Raises:
        DeviceError: if input field not a valid options

    """

    def __init__(self, device_info, **kwargs):

        self._info = device_info
        self._obj_ref = device_info.pop("obj_ref")
        self._obj_arg = device_info.pop("obj_arg")
        self.requires_cred = device_info.pop("requires_cred")
        if self.requires_cred and get_config("verify", self.vendor) != "True":
            prompt_lst = CONFIG_PROMPTS[self.vendor]
            for prompt in prompt_lst:
                set_config(*prompt)
        self.vendor_dlo = self._get_device(self._obj_ref, self._obj_arg)

    def _compat_run_input(self, run_input):
        """Checks if ``run_input`` is compatible with device and if not, calls transpiler."""
        device_run_package = self.info["run_package"]
        input_run_package = run_input.__module__.split(".")[0]
        if input_run_package != device_run_package:
            run_input = qbraid.circuit_wrapper(run_input).transpile(device_run_package)
        return run_input

    @property
    def info(self):
        """Return the device info."""
        return self._info

    @property
    def id(self):
        """Return the device ID."""
        return self.info["qbraid_id"]

    @property
    def name(self):
        """Return the device name.

        Returns:
            str: the name of the device.

        """
        return self.info["name"]

    @property
    def provider(self):
        """Return the device provider.

        Returns:
            str: the provider responsible for the device.

        """
        return self.info["provider"]

    @property
    def vendor(self):
        """Return the software vendor name.

        Returns:
            str: the name of the software vendor.

        """
        return self.info["vendor"]

    def __str__(self):
        return f"{self.vendor} {self.provider} {self.name} device wrapper"

    def __repr__(self):
        """String representation of a DeviceWrapper object."""
        return f"<{self.__class__.__name__}({self.provider}:'{self.name}')>"

    @abstractmethod
    def _get_device(self, obj_ref, obj_arg):
        """Abstract init device method."""

    @abstractmethod
    def run(self, run_input, *args, **kwargs):
        """Abstract run method."""

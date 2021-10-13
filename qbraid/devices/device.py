"""DeviceLikeWrapper Class"""

from abc import ABC, abstractmethod

import qbraid
from qbraid.devices._utils import verify_user

from .exceptions import DeviceError


class DeviceLikeWrapper(ABC):
    """Abstract interface for device-like classes."""

    def __init__(self, device_info, **kwargs):
        """Create a ``DeviceLikeWrapper`` object.

        Args:
            device_info (dict): device information dictionary containing the following fields:
                * qbraid_id (str): the internal device ID (see :func:`qbraid.get_devices`)
                * name (str): the name of the device
                * provider (str): the company to which the device belongs
                * vendor (str): the company who's software is used to access the device
                * run_package (str): the software package used to access the device
                * obj_ref (str): used internally to indicate the name of the object in run_package
                that corresponds to the device
                * obj_arg (str): used internally to indicate any arguments that need to be provided
                to the run_package object specified by obj_ref
                * requires_cred (bool): whether or not this device requires credentials for access
                * type (str): the type of the device, "QPU" or "Simulator"
                * qubits (int): the number of qubits in the device (if QPU)

        """
        self._info = device_info
        self._obj_ref = device_info.pop("obj_ref")
        self._obj_arg = device_info.pop("obj_arg")
        self._qubits = device_info["qubits"]
        self.requires_cred = device_info.pop("requires_cred")
        if self.requires_cred:
            verify_user(self.vendor)
        self.vendor_dlo = self._get_device()

    def _compat_run_input(self, run_input):
        """Checks if ``run_input`` is compatible with device and calls transpiler if necessary.

        Returns:
            run_input: the run_input e.g. a circuit object, possibly transpiled

        Raises:
            DeviceError: if devices is offline or if the number of qubits used in the circuit
            exceeds the number of qubits supported by the device.

        """
        if self.status.value == 1:
            raise DeviceError("Device is currently offline.")
        device_run_package = self.info["run_package"]
        input_run_package = run_input.__module__.split(".")[0]
        qbraid_circuit = qbraid.circuit_wrapper(run_input)
        if self.num_qubits and qbraid_circuit.num_qubits > self.num_qubits:
            raise DeviceError(
                f"Number of qubits in circuit ({qbraid_circuit.num_qubits}) exceeds "
                f"number of qubits in device ({self.num_qubits})."
            )
        if input_run_package != device_run_package:
            run_input = qbraid_circuit.transpile(device_run_package)
        compat_run_input = self._vendor_compat_run_input(run_input)
        return compat_run_input, qbraid_circuit

    @abstractmethod
    def _vendor_compat_run_input(self, run_input):
        """Applies any software/device specific modifications to run input."""

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

    @property
    def num_qubits(self):
        """The number of qubits supported by the device.

        Returns:
            int number of qubits supported by QPU. If Simulator returns None.

        """
        return self._qubits

    @property
    @abstractmethod
    def status(self):
        """Return device status."""

    def __str__(self):
        return f"{self.vendor} {self.provider} {self.name} device wrapper"

    def __repr__(self):
        """String representation of a DeviceWrapper object."""
        return f"<{self.__class__.__name__}({self.provider}:'{self.name}')>"

    @abstractmethod
    def _get_device(self):
        """Abstract init device method."""

    @abstractmethod
    def run(self, run_input, *args, **kwargs):
        """Abstract run method."""

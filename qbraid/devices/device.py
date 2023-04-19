# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint:disable=invalid-name

"""
Module defining abstract DeviceLikeWrapper Class

"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING  # pylint: disable=unused-import

from qbraid import circuit_wrapper

from .exceptions import DeviceError

if TYPE_CHECKING:
    import qbraid


class DeviceLikeWrapper(ABC):
    """Abstract interface for device-like classes."""

    def __init__(self, **kwargs):
        """Create a ``DeviceLikeWrapper`` object.

        Keyword Args:
            qbraid_id (str): The internal device ID (see :func:`~qbraid.get_devices`)
            name (str): The name of the device
            provider (str): The company to which the device belongs
            vendor (str): The company who's software is used to access the device
            runPackage (str): The software package used to access the device
            objArg (str): The vendor device id/arn to supply as argument to the vendor device-like object
            type (str): The type of the device, "QPU" or "Simulator"
            numberQubits (int): The number of qubits in the device (if applicable)

        """
        self._info = kwargs
        self._qubits = self._info["numberQubits"]
        self.vendor_device_id = self._info.pop("objArg")
        self.vendor_dlo = self._get_device()

    def _compat_run_input(self, run_input: "qbraid.QPROGRAM") -> "qbraid.QPROGRAM":
        """Checks if ``run_input`` is compatible with device and calls transpiler if necessary.

        Returns:
            :data:`~qbraid.QPROGRAM`: The run_input e.g. a circuit object, possibly transpiled

        Raises:
            DeviceError: If devices is offline or if the number of qubits used in the circuit
                exceeds the number of qubits supported by the device.

        """
        if self.status.value == 1:
            raise DeviceError("Device is currently offline.")
        device_run_package = self.info["runPackage"]
        input_run_package = run_input.__module__.split(".")[0]
        qbraid_circuit = circuit_wrapper(run_input)
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
    def info(self) -> dict:
        """Return the device info."""
        return self._info

    @property
    def id(self) -> str:
        """Return the device ID."""
        return self.info["qbraid_id"]

    @property
    def name(self) -> str:
        """Return the device name.

        Returns:
            The name of the device.

        """
        return self.info["name"]

    @property
    def provider(self) -> str:
        """Return the device provider.

        Returns:
            The provider responsible for the device.

        """
        return self.info["provider"]

    @property
    def vendor(self) -> str:
        """Return the software vendor name.

        Returns:
            The name of the software vendor.

        """
        return self.info["vendor"]

    @property
    def num_qubits(self) -> int:
        """The number of qubits supported by the device.

        Returns:
            Number of qubits supported by QPU. If Simulator returns None.

        """
        return self._qubits

    @property
    @abstractmethod
    def status(self) -> "qbraid.devices.DeviceStatus":
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
    def run(self, run_input: "qbraid.QPROGRAM", *args, **kwargs) -> "qbraid.devices.JobLikeWrapper":
        """Abstract run method."""

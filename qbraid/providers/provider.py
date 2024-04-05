# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for configuring provider credentials and authentication.

"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from qbraid_core.exceptions import AuthError
from qbraid_core.services.quantum import QuantumClient, QuantumServiceRequestError

from qbraid._import import _load_entrypoint

from ._import import QDEVICE_TYPES
from .exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    import qbraid.providers


class QuantumProvider(ABC):
    """
    This class is responsible for managing the interactions and
    authentications with various Quantum services.
    """

    @abstractmethod
    def save_config(self):
        """Save the current configuration."""

    @abstractmethod
    def get_devices(self):
        """Return a list of backends matching the specified filtering."""

    @abstractmethod
    def get_device(self, device_id: str):
        """Return quantum device corresponding to the specified device ID."""


class QbraidProvider(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with the AWS and IBM Quantum services.

    Attributes:
        aws_access_key_id (str): AWS access key ID for authenticating with AWS services.
        aws_secret_access_key (str): AWS secret access key for authenticating with AWS services.
        qiskit_ibm_token (str): IBM Quantum token for authenticating with IBM Quantum services.
    """

    def __init__(self, client: Optional[QuantumClient] = None, **kwargs):
        """
        Initializes the QbraidProvider object with optional AWS and IBM Quantum credentials.

        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access token. Defaults to None.
            qiskit_ibm_token (str, optional): IBM Quantum token. Defaults to None.
        """
        self._client = client
        aws_access_key_id = kwargs.get("aws_access_key_id", None)
        aws_secret_access_key = kwargs.get("aws_secret_access_key", None)
        qiskit_ibm_token = kwargs.get("qiskit_ibm_token", None)
        self._aws_provider = self._get_aws_provider(aws_access_key_id, aws_secret_access_key)
        self._ibm_provider = self._get_ibm_provider(qiskit_ibm_token)

    def save_config(self, **kwargs):
        """Save the current configuration."""
        self.client.session.save_config(**kwargs)

    @property
    def client(self):
        """Return the QuantumClient object."""
        if self._client is None:
            try:
                self._client = QuantumClient()
            except AuthError as err:
                raise ResourceNotFoundError(
                    "Failed to authenticate with the Quantum service."
                ) from err
        return self._client

    def _get_aws_provider(self, aws_access_key_id, aws_secret_access_key):
        if "braket.aws.aws_device.AwsDevice" not in QDEVICE_TYPES:
            return None

        from qbraid.providers.aws import BraketProvider  # pylint: disable=import-outside-toplevel

        try:
            return BraketProvider(aws_access_key_id, aws_secret_access_key)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def _get_ibm_provider(self, qiskit_ibm_token):
        if "qiskit_ibm_provider.ibm_backend.IBMBackend" not in QDEVICE_TYPES:
            return None

        from qbraid.providers.ibm import QiskitProvider  # pylint: disable=import-outside-toplevel

        try:
            return QiskitProvider(qiskit_ibm_token)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def _get_ibm_runtime(self, qiskit_ibm_token):
        if "qiskit_ibm_runtime.ibm_backend.IBMBackend" not in QDEVICE_TYPES:
            return None

        from qbraid.providers.ibm import QiskitRuntime  # pylint: disable=import-outside-toplevel

        try:
            return QiskitRuntime(qiskit_ibm_token)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def get_devices(self) -> "List[qbraid.providers.QDEVICE]":
        """Return a list of backends matching the specified filtering.

        Returns:
            list[QDEVICE]: a list of Backends that match the filtering
                criteria.
        """
        devices = []

        for provider in [self._aws_provider, self._ibm_provider]:
            if provider is not None:
                devices += provider.get_devices()

        return devices

    @staticmethod
    def _get_required_field(data: Dict[str, Any], field_name: str) -> Any:
        try:
            # For 'vendor', ensure it's a string and convert to lowercase
            if field_name == "vendor":
                return data[field_name].lower()
            return data[field_name]
        except KeyError as err:
            raise ResourceNotFoundError(
                "Failed to load device due to invalid device data: "
                f"missing required field '{field_name}'."
            ) from err
        except AttributeError as err:
            raise ResourceNotFoundError(
                "Failed to load device due to invalid device data: "
                f"field '{field_name}' is not properly formatted."
            ) from err

    def _get_vendor(self, vendor_device_id: str) -> str:
        """Return the software vendor of the specified device."""
        if vendor_device_id.startswith("ibm") or vendor_device_id.startswith("simulator"):
            return "ibm"
        if vendor_device_id.startswith("arn:aws"):
            return "aws"

        try:
            device_data = self.client.get_device(vendor_id=vendor_device_id)
        except (ValueError, QuantumServiceRequestError) as err:
            raise ResourceNotFoundError(f"Device {vendor_device_id} not found.") from err

        return self._get_required_field(device_data, "vendor")

    def _get_device(
        self, vendor_device_id: str, vendor: Optional[str] = None
    ) -> "qbraid.providers.QDEVICE":
        """Return quantum device corresponding to the specified device ID.

        Returns:
            QDEVICE: the quantum device corresponding to the given ID

        Raises:
            ResourceNotFoundError: if no device could be found
        """
        vendor = vendor or self._get_vendor(vendor_device_id)

        if vendor == "ibm" and self._ibm_provider is not None:
            return self._ibm_provider.get_device(vendor_device_id)

        if vendor == "aws" and self._aws_provider is not None:
            return self._aws_provider.get_device(vendor_device_id)

        raise ResourceNotFoundError(f"Device {vendor_device_id} not found.")

    def get_device(self, device_id: str) -> "qbraid.providers.QuantumDevice":
        """Return quantum device corresponding to the specified qBraid device ID.

        Returns:
            QuantumDevice: the quantum device corresponding to the given ID

        Raises:
            ResourceNotFoundError: if device cannot be loaded from quantum service data
        """
        first_error = None

        # Attempt to get the device data first with the qbraid_id and then with the vendor_id
        get_device_functions = [
            lambda: self.client.get_device(qbraid_id=device_id),
            lambda: self.client.get_device(vendor_id=device_id),
        ]

        for get_device_function in get_device_functions:
            try:
                device_data = get_device_function()
                break
            except (ValueError, QuantumServiceRequestError) as err:
                first_error = first_error or err
        else:
            raise ResourceNotFoundError(f"Device {device_id} not found.") from first_error

        # qbraid_device_id = self._get_required_field(device_data, "qbraid_id")
        vendor_device_id = self._get_required_field(device_data, "objArg")
        vendor = self._get_required_field(device_data, "vendor")

        device_obj = self._get_device(vendor_device_id, vendor)
        device_wrapper = _load_entrypoint("providers", f"{vendor}.device")
        return device_wrapper(device_obj)

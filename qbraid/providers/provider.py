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
from typing import List

from qbraid._qdevice import QDEVICE, QDEVICE_TYPES


class QbraidDeviceNotFoundError(Exception):
    """Exception raised when no device could be found."""


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
    def get_device(self, vendor_device_id: str):
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

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, qiskit_ibm_token=None):
        """
        Initializes the QbraidProvider object with optional AWS and IBM Quantum credentials.

        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access token. Defaults to None.
            qiskit_ibm_token (str, optional): IBM Quantum token. Defaults to None.
        """
        self._aws_provider = self._get_aws_provider(aws_access_key_id, aws_secret_access_key)
        self._ibm_provider = self._get_ibm_provider(qiskit_ibm_token)

    def save_config(self):
        raise NotImplementedError

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

    def get_devices(self) -> List[QDEVICE]:
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

    def get_device(self, vendor_device_id: str) -> QDEVICE:
        """Return quantum device corresponding to the specified device ID.

        Returns:
            QDEVICE: the quantum device corresponding to the given ID

        Raises:
            QbraidDeviceNotFoundError: if no device could be found
        """
        if vendor_device_id.startswith("ibm") or vendor_device_id.startswith("simulator"):
            if self._ibm_provider is not None:
                return self._ibm_provider.get_device(vendor_device_id)

        if vendor_device_id.startswith("arn:aws"):
            if self._aws_provider is not None:
                return self._aws_provider.get_device(vendor_device_id)

        raise QbraidDeviceNotFoundError(f"Device {vendor_device_id} not found.")

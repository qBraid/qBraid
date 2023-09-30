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

from typing import TYPE_CHECKING, List, Optional

from qbraid._qdevice import QDEVICE, QDEVICE_TYPES

if TYPE_CHECKING:
    import braket.aws
    import qiskit_ibm_provider


class QbraidDeviceNotFoundError(Exception):
    """Exception raised when no device could be found."""


class QbraidProvider:
    """
    This class is responsible for managing the interactions and
    authentications with the AWS and IBM Quantum services.

    Attributes:
        aws_access_key_id (str): AWS access key ID for authenticating with AWS services.
        aws_secret_access_key (str): AWS secret access key for authenticating with AWS services.
        ibm_quantum_token (str): IBM Quantum token for authenticating with IBM Quantum services.
    """

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, ibm_quantum_token=None):
        """
        Initializes the QbraidProvider object with optional AWS and IBM Quantum credentials.

        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access token. Defaults to None.
            ibm_quantum_token (str, optional): IBM Quantum token. Defaults to None.
        """
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.ibm_quantum_token = ibm_quantum_token

    def _get_ibm_provider(self) -> "qiskit_ibm_provider.IBMProvider":
        """Returns the IBM Quantum provider."""
        from qiskit_ibm_provider import IBMProvider  # pylint: disable=import-outside-toplevel

        return IBMProvider(token=self.ibm_quantum_token)

    def _get_ibm_backends(self) -> List["qiskit_ibm_provider.IBMBackend"]:
        """Returns the IBM Quantum provider backends."""
        provider = self._get_ibm_provider()
        return provider.backends(operational=True)

    def _get_ibm_backend(self, device_id: str) -> "qiskit_ibm_provider.IBMBackend":
        """Returns the IBM Quantum provider backends."""
        provider = self._get_ibm_provider()
        return provider.get_backend(device_id)

    @staticmethod
    def _get_default_region() -> str:
        """Returns the default AWS region."""
        from boto3.session import Session  # pylint: disable=import-outside-toplevel

        try:
            session = Session()
            return session.region_name
        except Exception:
            return "us-east-1"

    def _get_region_name(self, device_arn: str) -> str:
        """Returns the AWS region name."""
        REGIONS = ("us-east-1", "us-west-1", "us-west-2", "eu-west-2")

        maybe_region = device_arn.split(":")[3]
        if maybe_region in REGIONS:
            return maybe_region

        provider = device_arn.split("/")[-2]
        if provider in ["ionq", "quera", "xanadu"]:
            return "us-east-1"
        if provider == "oqc":
            return "eu-west-2"
        if provider == "rigetti":
            return "us-west-1"

        return self._get_default_region()

    def _get_aws_session(self, region_name: Optional[str] = None) -> "braket.aws.AwsSession":
        """Returns the AwsSession provider."""
        # pylint: disable=import-outside-toplevel
        from boto3.session import Session
        from braket.aws import AwsSession

        region_name = region_name or self._get_default_region()

        boto_session = Session(
            region_name=region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        return AwsSession(boto_session=boto_session)

    def _get_aws_devices(self) -> List["braket.aws.AwsDevice"]:
        """Returns the IBM Quantum provider backends."""
        from braket.aws import AwsDevice  # pylint: disable=import-outside-toplevel

        aws_session = self._get_aws_session()

        return AwsDevice.get_devices(aws_session=aws_session, statuses=["ONLINE", "OFFLINE"])

    def _get_aws_device(self, device_arn: str) -> "braket.aws.AwsDevice":
        """Returns the AWS device."""
        from braket.aws import AwsDevice  # pylint: disable=import-outside-toplevel

        region_name = self._get_region_name(device_arn)
        aws_session = self._get_aws_session(region_name=region_name)
        return AwsDevice(arn=device_arn, aws_session=aws_session)

    def get_devices(self) -> List[QDEVICE]:
        """Return a list of backends matching the specified filtering.

        Returns:
            list[QDEVICE]: a list of Backends that match the filtering
                criteria.
        """
        devices = []

        if "qiskit_ibm_provider.ibm_backend.IBMBackend" in QDEVICE_TYPES:
            devices += self._get_ibm_backends()

        if "braket.aws.aws_device.AwsDevice" in QDEVICE_TYPES:
            devices += self._get_aws_devices()

        return devices

    def get_device(self, vendor_device_id: str) -> QDEVICE:
        """Return quantum device corresponding to the specified device ID.

        Returns:
            QDEVICE: the quantum device corresponding to the given ID

        Raises:
            QbraidDeviceNotFoundError: if no device could be found
        """
        if vendor_device_id.startswith("ibm"):
            if "qiskit_ibm_provider.ibm_backend.IBMBackend" in QDEVICE_TYPES:
                return self._get_ibm_backend(vendor_device_id)

        if vendor_device_id.startswith("arn:aws"):
            if "braket.aws.aws_device.AwsDevice" in QDEVICE_TYPES:
                return self._get_aws_device(vendor_device_id)

        raise QbraidDeviceNotFoundError(f"Device {vendor_device_id} not found.")

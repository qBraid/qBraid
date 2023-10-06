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

import os
from typing import TYPE_CHECKING, List, Optional

from boto3.session import Session
from braket.aws import AwsDevice, AwsSession

if TYPE_CHECKING:
    import braket.aws


class BraketProvider:
    """
    This class is responsible for managing the interactions and
    authentications with the AWS services.

    Attributes:
        aws_access_key_id (str): AWS access key ID for authenticating with AWS services.
        aws_secret_access_key (str): AWS secret access key for authenticating with AWS services.
    """

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        """
        Initializes the QbraidProvider object with optional AWS credentials.

        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access token. Defaults to None.
        """
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")

    def save_config(self):
        """Save the current configuration."""
        raise NotImplementedError

    @staticmethod
    def _get_default_region() -> str:
        """Returns the default AWS region."""
        try:
            session = Session()
            return session.region_name
        except Exception:  # pylint: disable=broad-exception-caught
            return "us-east-1"

    @staticmethod
    def _get_s3_default_bucket() -> str:
        """Return name of the default bucket to use in the AWS Session"""
        try:
            aws_session = AwsSession()
            return aws_session.default_bucket()
        except Exception:  # pylint: disable=broad-exception-caught
            return "amazon-braket-qbraid-provider"

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
        region_name = region_name or self._get_default_region()
        default_bucket = self._get_s3_default_bucket()

        boto_session = Session(
            region_name=region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        return AwsSession(boto_session=boto_session, default_bucket=default_bucket)

    def get_devices(
        self, aws_session=None, statuses=None, **kwargs
    ) -> List["braket.aws.AwsDevice"]:
        """Return a list of backends matching the specified filtering."""
        aws_session = self._get_aws_session() if aws_session is None else aws_session
        statuses = ["ONLINE", "OFFLINE"] if statuses is None else statuses

        return AwsDevice.get_devices(aws_session=aws_session, statuses=statuses, **kwargs)

    def get_device(self, device_arn: str) -> "braket.aws.AwsDevice":
        """Returns the AWS device."""
        region_name = self._get_region_name(device_arn)
        aws_session = self._get_aws_session(region_name=region_name)
        return AwsDevice(arn=device_arn, aws_session=aws_session)

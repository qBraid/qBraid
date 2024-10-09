# Copyright (C) 2024 qBraid
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
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Optional

import boto3
from boto3.session import Session
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.aws import AwsDevice, AwsSession
from braket.circuits import Circuit
from qbraid_core.services.quantum import quantum_lib_proxy_state
from qbraid_core.services.quantum.proxy_braket import aws_configure

from qbraid._caching import cached_method
from qbraid.exceptions import QbraidError
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime import QuantumProvider, TargetProfile

from .device import BraketDevice

if TYPE_CHECKING:
    import braket.aws

    import qbraid.runtime.aws


class BraketProvider(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with the AWS services.

    Attributes:
        aws_access_key_id (str): AWS access key ID for authenticating with AWS services.
        aws_secret_access_key (str): AWS secret access key for authenticating with AWS services.
    """

    REGIONS = ("us-east-1", "us-west-1", "us-west-2", "eu-west-2")

    def __init__(
        self, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None
    ):
        """
        Initializes the QbraidProvider object with optional AWS credentials.

        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access token. Defaults to None.
        """
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")

    def save_config(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        **kwargs,
    ):
        """Save the current configuration."""
        aws_access_key_id = aws_access_key_id or self.aws_access_key_id
        aws_secret_access_key = aws_secret_access_key or self.aws_secret_access_key
        aws_configure(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            **kwargs,
        )

    @staticmethod
    def _get_default_region() -> str:
        """Returns the default AWS region."""
        default_region = "us-east-1"

        try:
            session = Session()
            return session.region_name or default_region
        except Exception:  # pylint: disable=broad-exception-caught
            return default_region

    @staticmethod
    def _get_s3_default_bucket() -> str:
        """Return name of the default bucket to use in the AWS Session"""
        try:
            aws_session = AwsSession()
            return aws_session.default_bucket()
        except Exception:  # pylint: disable=broad-exception-caught
            return "amazon-braket-qbraid-jobs"

    def _get_aws_session(self, region_name: Optional[str] = None) -> braket.aws.AwsSession:
        """Returns the AwsSession provider."""
        region_name = region_name or self._get_default_region()
        default_bucket = self._get_s3_default_bucket()

        boto_session = Session(
            region_name=region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        braket_client = boto_session.client("braket", region_name=region_name)
        return AwsSession(
            boto_session=boto_session, braket_client=braket_client, default_bucket=default_bucket
        )

    def _build_runtime_profile(
        self, device: braket.aws.AwsDevice, program_spec: Optional[ProgramSpec] = None, **kwargs
    ) -> TargetProfile:
        """Returns the runtime profile for the device."""
        metadata = device.aws_session.get_device(device.arn)
        simulator = metadata.get("deviceType") == "SIMULATOR"
        provider_name = metadata.get("providerName")
        capabilities: dict = json.loads(metadata.get("deviceCapabilities"))
        paradigm: dict = capabilities.get("paradigm", {})
        action: dict = capabilities.get("action", {})
        num_qubits = paradigm.get("qubitCount")
        if action.get("braket.ir.openqasm.program") is not None:
            experiment_type = ExperimentType.GATE_MODEL
            program_spec = program_spec or ProgramSpec(Circuit)
        elif action.get("braket.ir.ahs.program") is not None:
            experiment_type = ExperimentType.AHS
            program_spec = program_spec or ProgramSpec(
                AnalogHamiltonianSimulation, alias="braket_ahs"
            )
        else:
            raise QbraidError(
                f"TargetProfile cannot be created for device '{device.arn}' as it does not "
                f"support 'braket.ir.openqasm.program' program types. Please verify device "
                f"capabilities or select a different, compatible device."
            )
        return TargetProfile(
            simulator=simulator,
            num_qubits=num_qubits,
            experiment_type=experiment_type,
            program_spec=program_spec,
            provider_name=provider_name,
            device_id=device.arn,
            **kwargs,
        )

    @cached_method
    def get_devices(
        self,
        aws_session: Optional[braket.aws.AwsSession] = None,
        statuses: Optional[list[str]] = None,
        **kwargs,
    ) -> list[qbraid.runtime.aws.BraketDevice]:
        """Return a list of backends matching the specified filtering."""
        aws_session = self._get_aws_session() if aws_session is None else aws_session
        statuses = ["ONLINE", "OFFLINE"] if statuses is None else statuses
        aws_devices = AwsDevice.get_devices(aws_session=aws_session, statuses=statuses, **kwargs)
        return [
            BraketDevice(profile=self._build_runtime_profile(device), session=device.aws_session)
            for device in aws_devices
        ]

    @cached_method
    def get_device(
        self,
        device_id: str,
    ) -> qbraid.runtime.aws.BraketDevice:
        """Returns the AWS device."""
        try:
            region_name = device_id.split(":")[3]
        except IndexError as err:
            raise ValueError(
                f"Device ARN is not a valid format: {device_id}. For valid Braket ARNs, "
                "see 'https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html'"
            ) from err
        region_name = region_name or self._get_default_region()
        aws_session = self._get_aws_session(region_name=region_name)
        device = AwsDevice(arn=device_id, aws_session=aws_session)
        profile = self._build_runtime_profile(device)
        return BraketDevice(profile=profile, session=device.aws_session)

    @staticmethod
    def _fetch_resources(region_names: list[str], key: str, values: list[str]) -> list[str]:
        """Fetch resources from AWS."""
        tasks = []
        for region_name in region_names:
            client = boto3.client("resourcegroupstaggingapi", region_name=region_name)
            response = client.get_resources(
                TagFilters=[
                    {
                        "Key": key,
                        "Values": values,
                    }
                ],
            )
            matches = [t["ResourceARN"] for t in response["ResourceTagMappingList"]]
            tasks += matches
        return tasks

    def get_tasks_by_tag(
        self, key: str, values: Optional[list[str]] = None, region_names: Optional[list[str]] = None
    ) -> list[str]:
        """
        Retrieves a list of quantum task ARNs that match the specified tag keys or key/value pairs.

        Args:
            key (str): The tag key to match.
            values (Optional[list[str]]): A list of tag values to match against the provided
                                          key. If None, tasks with the specified key,
                                          regardless of its value, are matched.
            region_names (Optional[list[str]]): A list of region names to search. If None, all
                                                regions in `self.REGIONS` are searched.

        Returns:
            list[str]: A list of ARNs for quantum tasks that match the given tag criteria.

        Raises:
            QbraidError: If the function is called within a qBraid quantum job environment
                         where AWS S3 requests are not supported.
        """
        try:
            jobs_state = quantum_lib_proxy_state("braket")
            jobs_enabled = jobs_state.get("enabled", False)
        except ValueError:
            jobs_enabled = False

        if jobs_enabled:
            raise QbraidError("AWS S3 requests not supported by qBraid quantum jobs.")

        region_names = (
            region_names
            if region_names is not None and len(region_names) > 0
            else list(self.REGIONS)
        )
        values = values if values is not None else []

        return self._fetch_resources(region_names, key, values)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(
                self, "_hash", hash((self.aws_access_key_id, self.aws_secret_access_key))
            )
        return self._hash  # pylint: disable=no-member

# Copyright 2025 qBraid
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

"""
Module for configuring provider credentials and authentication.

"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import boto3
from boto3.session import Session
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.aws import AwsDevice, AwsSession
from braket.circuits import Circuit

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
        aws_session_token (str): AWS session token for authenticating with AWS services when using
            temporary credentials.
    """

    REGIONS = ("us-east-1", "us-west-1", "us-west-2", "eu-west-2")

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
    ):
        """
        Initializes the QbraidProvider object with optional AWS credentials.

        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access token. Defaults to None.
            aws_session_token (str, optional): AWS session token. Defaults to None.
        """
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = aws_session_token

    @staticmethod
    def aws_configure(
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region: str | None = None,
    ) -> None:
        """
        Initializes and populates AWS configuration and credentials files.

        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access key. Defaults to None.
            region (str, optional): AWS region. Defaults to None.
        """
        aws_dir = Path.home() / ".aws"
        config_path = aws_dir / "config"
        credentials_path = aws_dir / "credentials"
        aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID", "MYACCESSKEY")
        aws_secret_access_key = aws_secret_access_key or os.getenv(
            "AWS_SECRET_ACCESS_KEY", "MYSECRETKEY"
        )
        region = region or os.getenv("AWS_REGION", "us-east-1")

        aws_dir.mkdir(exist_ok=True)
        if not config_path.exists():
            config_content = f"[default]\nregion = {region}\noutput = json\n"
            config_path.write_text(config_content)
        if not credentials_path.exists():
            credentials_content = (
                f"[default]\n"
                f"aws_access_key_id = {aws_access_key_id}\n"
                f"aws_secret_access_key = {aws_secret_access_key}\n"
            )
            credentials_path.write_text(credentials_content)

    def save_config(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        **kwargs,
    ):
        """Save the current configuration."""
        aws_access_key_id = aws_access_key_id or self.aws_access_key_id
        aws_secret_access_key = aws_secret_access_key or self.aws_secret_access_key
        BraketProvider.aws_configure(
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
        region_name = region_name or os.environ.get("AWS_REGION") or self._get_default_region()
        default_bucket = self._get_s3_default_bucket()

        boto_session = Session(
            region_name=region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
        )
        braket_client = boto_session.client(
            "braket", region_name=region_name, endpoint_url=os.environ.get("BRAKET_ENDPOINT")
        )
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
        basis_gates = paradigm.get("nativeGateSet", None)
        if action.get("braket.ir.openqasm.program") is not None:
            experiment_type = ExperimentType.GATE_MODEL
            program_spec = program_spec or ProgramSpec(Circuit)
        elif action.get("braket.ir.ahs.program") is not None:
            experiment_type = ExperimentType.ANALOG
            program_spec = program_spec or ProgramSpec(
                AnalogHamiltonianSimulation, alias="braket_ahs"
            )
        else:
            raise QbraidError(
                f"TargetProfile cannot be created for device '{device.arn}' as it does not "
                "support 'braket.ir.openqasm.program' or 'braket.ir.ahs.program' types. "
                "Please verify device capabilities or select a different, compatible device."
            )
        return TargetProfile(
            simulator=simulator,
            num_qubits=num_qubits,
            experiment_type=experiment_type,
            program_spec=program_spec,
            provider_name=provider_name,
            device_id=device.arn,
            basis_gates=basis_gates,
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
        region_names = (
            region_names
            if region_names is not None and len(region_names) > 0
            else list(self.REGIONS)
        )
        values = values if values is not None else []

        return self._fetch_resources(region_names, key, values)

    @staticmethod
    def _serialize_task(task: dict[str, Any]) -> dict[str, Any]:
        """Convert datetime objects in a task dict to ISO strings for JSON serialization."""

        return {k: v.isoformat() if isinstance(v, datetime) else v for k, v in task.items()}

    def _search_tasks(
        self,
        region: str,
        limit: int = 20,
        status: Optional[str] = None,
        device_arn: Optional[str] = None,
        next_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute a single search_quantum_tasks call for a specific region."""
        aws_session = self._get_aws_session(region_name=region)
        client = aws_session.boto_session.client("braket", region_name=region)

        kwargs: dict[str, Any] = {"maxResults": limit}
        if next_token:
            kwargs["nextToken"] = next_token

        filters: list[dict[str, Any]] = []
        if status:
            filters.append({"name": "status", "operator": "EQUAL", "values": [status]})
        if device_arn:
            filters.append({"name": "deviceArn", "operator": "EQUAL", "values": [device_arn]})
        kwargs["filters"] = filters

        response = client.search_quantum_tasks(**kwargs)
        return {
            "tasks": [self._serialize_task(t) for t in response.get("quantumTasks", [])],
            "nextToken": response.get("nextToken"),
        }

    def list_jobs(
        self,
        limit: int = 20,
        status: Optional[str] = None,
        device_arn: Optional[str] = None,
        device_arns: Optional[list[str]] = None,
        next_token: Optional[str] = None,
        region: Optional[str] = None,
        tags: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """List quantum tasks from Amazon Braket.

        Args:
            limit: Maximum number of tasks to return.
            status: Filter by status (COMPLETED, FAILED, RUNNING, QUEUED, CANCELLED, etc.).
            device_arn: Filter by a single device ARN.
            device_arns: Filter by multiple device ARNs (e.g. all devices from a provider).
                Tasks matching any of the ARNs are returned. Each ARN may be in a
                different region — the method queries each region automatically.
            next_token: Pagination token from a previous call (only works with
                single-device or no-device filters, not with device_arns).
            region: AWS region. Defaults to provider's default region.
            tags: Filter by tags. Dict of {key: value} pairs. Tasks must match
                all specified tags. Uses the AWS resource tagging API.

        Returns:
            Dict with ``tasks`` (list of task dicts) and ``nextToken`` (for pagination).
        """
        # Multi-device filter: query each device ARN (possibly across regions)
        # and merge results, sorted by creation time descending
        if device_arns:
            all_tasks: list[dict[str, Any]] = []
            for arn in device_arns:
                # Extract region from ARN
                try:
                    arn_region = arn.split(":")[3]
                except IndexError:
                    arn_region = ""
                arn_region = arn_region or self._get_default_region()

                result = self._search_tasks(
                    region=arn_region,
                    limit=limit,
                    status=status,
                    device_arn=arn,
                )
                all_tasks.extend(result.get("tasks", []))

            # Sort by creation time descending and trim to limit
            all_tasks.sort(
                key=lambda t: t.get("createdAt", ""),
                reverse=True,
            )
            return {
                "tasks": all_tasks[:limit],
                "nextToken": None,  # pagination not supported for multi-device queries
            }

        # Single device or no device filter: straightforward query
        region = region or self._get_default_region()

        # Auto-detect region from device ARN if not specified
        if device_arn and not region:
            try:
                arn_region = device_arn.split(":")[3]
                if arn_region:
                    region = arn_region
            except IndexError:
                pass

        result = self._search_tasks(
            region=region,
            limit=limit,
            status=status,
            device_arn=device_arn,
            next_token=next_token,
        )
        tasks = result["tasks"]

        # If tag filter requested, narrow results using resource tagging API
        if tags:
            tagged_arns: set[str] = set()
            for key, value in tags.items():
                arns = self.get_tasks_by_tag(
                    key=key,
                    values=[value] if value else None,
                    region_names=[region],
                )
                if not tagged_arns:
                    tagged_arns = set(arns)
                else:
                    tagged_arns &= set(arns)

            tasks = [t for t in tasks if t.get("quantumTaskArn") in tagged_arns]

        return {
            "tasks": tasks,
            "nextToken": result.get("nextToken"),
        }

    def get_job(self, task_arn: str) -> dict[str, Any]:
        """Get a single quantum task from Amazon Braket.

        Args:
            task_arn: Quantum task ARN.

        Returns:
            Task dict with full details.
        """
        # Parse region from ARN: arn:aws:braket:<region>:...
        try:
            region = task_arn.split(":")[3]
        except IndexError:
            region = self._get_default_region()
        region = region or self._get_default_region()

        aws_session = self._get_aws_session(region_name=region)
        client = aws_session.boto_session.client("braket", region_name=region)
        response = client.get_quantum_task(quantumTaskArn=task_arn)
        return self._serialize_task(response)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(
                self,
                "_hash",
                hash((self.aws_access_key_id, self.aws_secret_access_key, self.aws_session_token)),
            )
        return self._hash  # pylint: disable=no-member

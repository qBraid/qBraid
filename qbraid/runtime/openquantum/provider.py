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
Module defining OpenQuantum session and provider classes

"""
import os
import time
from typing import Any, Callable, Optional

import requests
from qbraid_core.sessions import Session

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import OpenQuantumDevice


class OpenQuantumSession(Session):
    """OpenQuantum session class."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_provider: Optional[Callable[[], tuple[str, float]]] = None,
    ):
        # token_provider lets a caller supply (access_token, expires_at_epoch) on
        # demand — used to act as a specific user's linked OpenQuantum account
        # instead of qBraid's own client_credentials identity. When set, the
        # client_credentials grant (and so client_id/secret) is not needed.
        self._token_provider = token_provider

        if token_provider is None:
            self.client_id = client_id or os.getenv("OPENQUANTUM_CLIENT_ID")
            self.client_secret = client_secret or os.getenv("OPENQUANTUM_CLIENT_SECRET")

            if not self.client_id or not self.client_secret:
                raise ValueError(
                    "OpenQuantum client_id and client_secret are required. "
                    "Set OPENQUANTUM_CLIENT_ID and OPENQUANTUM_CLIENT_SECRET environment variables."
                )
        else:
            self.client_id = client_id
            self.client_secret = client_secret

        self.auth_url = "https://id.openquantum.com"
        self.scheduler_url = "https://scheduler.openquantum.com"
        self.management_url = "https://management.openquantum.com"

        super().__init__(base_url=self.scheduler_url)
        self._token = None
        self._token_expires_at = 0

    def _fetch_token(self):
        if self._token_provider is not None:
            self._token, self._token_expires_at = self._token_provider()
            return
        url = f"{self.auth_url}/realms/platform/protocol/openid-connect/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 300)

    def _ensure_token(self):
        if not self._token or time.time() >= self._token_expires_at - 30:
            self._fetch_token()

    def request(self, method, url, *args, **kwargs):
        self._ensure_token()
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        kwargs["headers"] = headers
        return super().request(method, url, *args, **kwargs)

    def get_devices(self) -> list[dict[str, Any]]:
        """Get all OpenQuantum devices."""
        url = f"{self.management_url}/v1/backends/classes"
        devices = []
        cursor = None
        while True:
            params = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            resp = self.get(url, params=params).json()
            devices.extend(resp.get("backend_classes", []))
            cursor = resp.get("pagination", {}).get("next_cursor")
            if not cursor:
                break
        return devices

    def get_backend_class_details(self, backend_id: str) -> dict[str, Any]:
        """Get detailed information for a specific backend class."""
        url = f"{self.scheduler_url}/v1/backends/classes/{backend_id}"
        return self.get(url).json()

    def get_user_organizations(self) -> list[dict[str, Any]]:
        """Get user organizations."""
        url = f"{self.management_url}/v1/users/organizations"
        resp = self.get(url, params={"limit": 10}).json()
        return resp.get("organizations", [])

    def upload_input(self, content: bytes) -> str:
        """Upload input file content."""
        url = f"{self.scheduler_url}/v1/jobs/upload"
        resp = self.post(url).json()
        upload_id = resp["id"]
        upload_url = resp["url"]
        requests.put(upload_url, data=content, timeout=60).raise_for_status()
        return upload_id

    def prepare_job(self, data: dict[str, Any]) -> dict[str, Any]:
        """Prepare a job."""
        url = f"{self.scheduler_url}/v1/jobs/prepare"
        return self.post(url, json=data).json()

    def get_preparation_result(self, prep_id: str) -> dict[str, Any]:
        """Get job preparation result."""
        url = f"{self.scheduler_url}/v1/jobs/prepare/{prep_id}"
        return self.get(url).json()

    def wait_for_preparation(self, prep_id: str, timeout: int = 300) -> list[dict[str, Any]]:
        """Wait for job preparation to complete and return the quote."""
        start = time.time()
        while time.time() - start < timeout:
            res = self.get_preparation_result(prep_id)
            status = res["status"]
            if status == "Completed":
                return res["quote"]
            if status == "Failed":
                raise ValueError(f"Job preparation failed: {res.get('message')}")
            time.sleep(2)
        raise TimeoutError("Job preparation timed out.")

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new job."""
        url = f"{self.scheduler_url}/v1/jobs"
        return self.post(url, json=data).json()

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Get a specific job."""
        url = f"{self.scheduler_url}/v1/jobs/{job_id}"
        return self.get(url).json()

    def cancel_job(self, job_id: str) -> None:
        """Cancel a job."""
        url = f"{self.scheduler_url}/v1/jobs/{job_id}"
        self.delete(url).raise_for_status()

    def download_job_output(self, job_id: str) -> dict[str, Any]:
        """Download job output."""
        job = self.get_job(job_id)
        output_url = job.get("output_data_url")
        if not output_url:
            raise ResourceNotFoundError("Job output URL not available.")

        response = requests.get(output_url, timeout=60)
        response.raise_for_status()
        return response.json()


class OpenQuantumProvider(QuantumProvider):
    """OpenQuantum provider class."""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.session = OpenQuantumSession(client_id, client_secret)

    def _build_profile(self, data: dict[str, Any]) -> TargetProfile:
        device_id = data.get("short_code") or data.get("id")
        # Extract max_qubits from constraint_data if available
        constraint_data = data.get("constraint_data")
        num_qubits = constraint_data.get("max_qubits") if constraint_data else None

        return TargetProfile(
            device_id=device_id,
            simulator=data.get("type") == "SIMULATOR",
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=num_qubits,
            constraint_data=constraint_data,
            program_spec=[
                ProgramSpec(str, alias="qasm3", experiment_type=ExperimentType.GATE_MODEL),
                ProgramSpec(str, alias="qasm2", experiment_type=ExperimentType.GATE_MODEL),
            ],
            provider_name="Open Quantum",
        )

    @cached_method
    def get_devices(self) -> list[OpenQuantumDevice]:
        """Get a list of OpenQuantum devices."""
        data = self.session.get_devices()
        # Enrich each device with constraint data from details API
        enriched_devices = []
        for device in data:
            device_id = device.get("id")
            if device_id:
                try:
                    details = self.session.get_backend_class_details(device_id)
                    # Merge constraint_data from details into device data
                    if "constraint_data" in details:
                        device["constraint_data"] = details["constraint_data"]
                except Exception:  # pylint: disable=broad-exception-caught
                    # If details API fails, continue with basic device data
                    pass
            enriched_devices.append(device)
        return [OpenQuantumDevice(self._build_profile(d), self.session) for d in enriched_devices]

    @cached_method
    def get_device(self, device_id: str) -> OpenQuantumDevice:
        """Get a specific OpenQuantum device."""
        devices = self.get_devices()
        for device in devices:
            if device.id == device_id:
                return device
        raise ResourceNotFoundError(f"Device '{device_id}' not found.")

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(
                self,
                "_hash",
                hash((self.session.client_id, self.session.client_secret, self.session.base_url)),
            )
        return self._hash  # pylint: disable=no-member

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
Module for configuring IBM provider credentials and authentication.

"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import qiskit
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.accounts import ChannelType

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import AuthorizationError, JobNotFoundError, RuntimeAPIError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import QiskitBackend

if TYPE_CHECKING:
    import qiskit_ibm_runtime

    import qbraid.runtime.ibm

logger = logging.getLogger(__name__)

# IBM Cloud endpoints for direct REST API access
_IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
_IBM_RUNTIME_BASE = "https://us-east.quantum-computing.cloud.ibm.com"


class _IBMError(NamedTuple):
    """The parts of IBM's ``ErrorContainer`` response body that we surface."""

    error_code: Optional[str]
    message: Optional[str]
    trace: Optional[str]
    solution: Optional[str]
    more_info: Optional[str]


def _parse_ibm_error(error: HTTPError) -> tuple[bool, Optional[_IBMError]]:
    """Parse IBM's ``ErrorContainer`` error body, if that is what came back.

    Returns a ``(has_body, parsed)`` pair:

    * ``(False, None)`` — the response carried no readable body, so the HTTP status
      is all we have to go on.
    * ``(True, None)`` — a body came back, but it is not an ``ErrorContainer``. It
      therefore did not come from the Runtime API: an edge proxy in front of IBM
      answers with an HTML block page, and a 403 from *that* says nothing about
      whether the caller's credentials are valid.
    * ``(True, _IBMError(...))`` — IBM's own structured error.
    """
    try:
        raw = error.read()
    except (AttributeError, OSError):  # fp is None, or the stream is already consumed
        return False, None
    if not raw:
        return False, None

    try:
        body = json.loads(raw)
        errors = body["errors"]
        first = errors[0]
    except (ValueError, TypeError, LookupError):
        return True, None

    code = first.get("code")
    return True, _IBMError(
        # IBM's OpenAPI spec declares `code` a string, but the API sends an int.
        error_code=None if code is None else str(code),
        message=first.get("message"),
        trace=body.get("trace") if isinstance(body, dict) else None,
        # `solution` is absent from IBM's published ErrorContainer schema, but the API
        # does send it. Treat it as best-effort: read it if it's there, never rely on it.
        solution=first.get("solution"),
        more_info=first.get("more_info"),
    )


class QiskitRuntimeProvider(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with the IBM Quantum services.

    Attributes:
        runtime_service (qiskit_ibm_runtime.QiskitRuntimeService): IBM Quantum runtime service.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        instance: Optional[str] = None,
        channel: Optional[ChannelType] = None,
        **kwargs,
    ):
        """
        Initializes the QiskitRuntimeProvider object with IBM Quantum credentials.

        Args:
            token (str, optional): IBM Cloud API key.
            instance (str, optional): The service instance to use.
                This is the Cloud Resource Name (CRN) or the service name. If set, it will define
                a default instance for service instantiation. If not set, the service will fetch
                all instances accessible within the account.
            channel (ChannelType, optional): ``ibm_cloud``, ``ibm_quantum_platform`` or ``local``.
                If ``local``, uses testing mode and primitive queries will run on local simulator.
        """
        self.token = token or os.getenv("QISKIT_IBM_TOKEN")
        self.instance = instance or os.getenv("QISKIT_IBM_INSTANCE")
        self.channel = channel or os.getenv("QISKIT_IBM_CHANNEL", "ibm_quantum_platform")
        self._runtime_service = QiskitRuntimeService(
            channel=self.channel, token=self.token, instance=self.instance, **kwargs
        )

    @property
    def runtime_service(self) -> qiskit_ibm_runtime.QiskitRuntimeService:
        """Returns the IBM Quantum runtime service."""
        return self._runtime_service

    def save_config(
        self,
        token: Optional[str] = None,
        instance: Optional[str] = None,
        channel: Optional[ChannelType] = None,
        overwrite: bool = True,
        **kwargs,
    ) -> None:
        """Saves IBM runtime service account to disk for future use."""
        token = token or self.token
        instance = instance or self.instance
        channel = channel or self.channel
        QiskitRuntimeService.save_account(
            token=token, instance=instance, channel=channel, overwrite=overwrite, **kwargs
        )

    def _build_runtime_profile(
        self, backend: qiskit_ibm_runtime.IBMBackend, program_spec: Optional[ProgramSpec] = None
    ) -> TargetProfile:
        """Builds a runtime profile from a backend."""
        program_spec = program_spec or ProgramSpec(qiskit.QuantumCircuit)
        config = backend.configuration()

        local = config.local
        simulator = config.local or config.simulator

        return TargetProfile(
            device_id=backend.name,
            simulator=simulator,
            local=local,
            num_qubits=config.n_qubits,
            program_spec=program_spec,
            instance=backend._instance,
            max_shots=config.max_shots,
            provider_name="IBM",
            experiment_type=ExperimentType.GATE_MODEL,
            basis_gates=config.basis_gates,
        )

    @cached_method
    def get_devices(self, operational=True, **kwargs) -> list[qbraid.runtime.ibm.QiskitBackend]:
        """Returns the IBM Quantum provider backends."""

        backends = self.runtime_service.backends(operational=operational, **kwargs)
        program_spec = ProgramSpec(qiskit.QuantumCircuit)
        return [
            QiskitBackend(
                profile=self._build_runtime_profile(backend, program_spec=program_spec),
                service=self.runtime_service,
            )
            for backend in backends
        ]

    @cached_method
    def get_device(
        self, device_id: str, instance: Optional[str] = None
    ) -> qbraid.runtime.ibm.QiskitBackend:
        """Returns the IBM Quantum provider backends."""
        backend = self.runtime_service.backend(device_id, instance=instance)
        return QiskitBackend(
            profile=self._build_runtime_profile(backend), service=self.runtime_service
        )

    def least_busy(
        self, simulator=False, operational=True, **kwargs
    ) -> qbraid.runtime.ibm.QiskitBackend:
        """Return the least busy IBMQ QPU."""
        backend = self.runtime_service.least_busy(
            simulator=simulator, operational=operational, **kwargs
        )
        return QiskitBackend(
            profile=self._build_runtime_profile(backend), service=self.runtime_service
        )

    @staticmethod
    def _load_ibm_cloud_credentials() -> dict[str, str]:
        """Load IBM Cloud credentials from ~/.qiskit/qiskit-ibm.json."""

        config_path = Path.home() / ".qiskit" / "qiskit-ibm.json"
        if not config_path.exists():
            return {}

        try:
            data = json.loads(config_path.read_text())
            # Prefer ibm_cloud channel, fall back to first entry
            for entry in data.values():
                if entry.get("channel") == "ibm_cloud":
                    return {
                        "token": entry.get("token", ""),
                        "instance": entry.get("instance", ""),
                    }
            if data:
                first = next(iter(data.values()))
                return {
                    "token": first.get("token", ""),
                    "instance": first.get("instance", ""),
                }
        except (json.JSONDecodeError, OSError) as e:
            logger.debug("Failed to load IBM credentials: %s", e)

        return {}

    def _exchange_api_key(self) -> str:
        """Exchange IBM Cloud API key for an IAM access token."""
        # Try explicit token, then runtime service, then config file
        token = self.token
        if not token:
            try:
                token = self._runtime_service._account.token
            except AttributeError:
                pass
        if not token:
            creds = self._load_ibm_cloud_credentials()
            token = creds.get("token")
        if not token:
            raise ValueError("IBM API key not found. Set QISKIT_IBM_TOKEN or pass token directly.")

        data = urlencode(
            {
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": token,
            }
        ).encode("utf-8")

        req = Request(_IAM_TOKEN_URL, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                access_token = result.get("access_token")
                if not access_token:
                    raise ValueError("No access_token in IAM response")
                return access_token
        except HTTPError as e:
            # IAM rejects a bad/expired API key with 400 or 401 — that's a
            # credentials problem, not a generic failure.
            message = f"Failed to exchange IBM API key: {e}"
            if e.code in (400, 401, 403):
                raise AuthorizationError(message, status_code=e.code) from e
            raise RuntimeAPIError(message, status_code=e.code) from e
        except (URLError, OSError) as e:
            raise RuntimeAPIError(f"Failed to exchange IBM API key: {e}") from e

    def _ibm_api_get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Make an authenticated GET request to the IBM Runtime API."""
        access_token = self._exchange_api_key()
        instance = self.instance
        if not instance:
            try:
                instance = self._runtime_service._account.instance
            except AttributeError:
                pass
        if not instance:
            creds = self._load_ibm_cloud_credentials()
            instance = creds.get("instance")
        if not instance:
            raise ValueError("IBM Cloud instance (CRN) not found.")

        url = f"{_IBM_RUNTIME_BASE}{path}"
        if params:
            # doseq=True so list values (e.g. tags=[...]) serialize as repeated
            # query params (tags=a&tags=b) instead of the literal "['a', 'b']".
            url += "?" + urlencode(params, doseq=True)

        req = Request(url)
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("Service-CRN", instance)
        req.add_header("Accept", "application/json")
        from qbraid._version import __version__  # pylint: disable=import-outside-toplevel

        req.add_header("User-Agent", f"qbraid/{__version__}")

        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            # Preserve the provider's status code in the exception type so callers
            # can tell "this job doesn't exist" apart from "your credentials were
            # rejected" without parsing the message text.
            has_body, detail = _parse_ibm_error(e)
            message = f"IBM API request failed: {e}"
            if detail and detail.message:
                message = f"IBM API request failed ({e.code}): {detail.message}"
            kwargs: dict[str, Any] = {"status_code": e.code}
            if detail:
                kwargs.update(
                    error_code=detail.error_code,
                    trace=detail.trace,
                    solution=detail.solution,
                    more_info=detail.more_info,
                )

            if e.code == 404:
                raise JobNotFoundError(message, **kwargs) from e
            # Only IBM can tell us that credentials were rejected. A 401/403 carrying
            # a body that is not an ErrorContainer came from an edge proxy, not the
            # API, and the caller's credentials may be perfectly valid -- reporting
            # that as an AuthorizationError is what sends users off to re-save
            # working credentials.
            if e.code in (401, 403) and not (has_body and detail is None):
                raise AuthorizationError(message, **kwargs) from e
            raise RuntimeAPIError(message, **kwargs) from e
        except (URLError, OSError) as e:
            # No HTTP response at all (DNS failure, timeout, connection reset).
            raise RuntimeAPIError(f"IBM API request failed: {e}") from e

    def list_jobs(  # pylint: disable=too-many-arguments
        self,
        limit: int = 20,
        offset: int = 0,
        pending: Optional[bool] = None,
        backend: Optional[str] = None,
        tags: Optional[list[str]] = None,
        program: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        sort: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """List jobs from IBM Quantum.

        Args:
            limit: Maximum number of jobs to return (max 200).
            offset: Number of jobs to skip (for pagination).
            pending: If True, return queued/running jobs. If False, return
                completed/cancelled/failed jobs. If None, return all.
            backend: Filter by backend name.
            tags: Filter by tags (list of tag strings).
            program: Filter by program ID.
            created_after: Filter jobs created after this datetime (ISO format).
            created_before: Filter jobs created before this datetime (ISO format).
            sort: Sort by created time ("ASC" or "DESC", default "DESC").
            session_id: Filter by session ID.

        Returns:
            Dict with ``jobs`` (list of job dicts) and ``count`` (total jobs).
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if pending is not None:
            params["pending"] = str(pending).lower()
        if backend:
            params["backend"] = backend
        if tags:
            params["tags"] = tags
        if program:
            params["program"] = program
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        if sort:
            params["sort"] = sort
        if session_id:
            params["session_id"] = session_id

        data = self._ibm_api_get("/jobs", params)
        return {
            "jobs": data.get("jobs", []),
            "count": data.get("count", len(data.get("jobs", []))),
        }

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Get a single job from IBM Quantum.

        Args:
            job_id: IBM job ID.

        Returns:
            Job dict with full details.
        """
        return self._ibm_api_get(f"/jobs/{job_id}")

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(self, "_hash", hash((self.token, self.channel)))
        return self._hash  # pylint: disable=no-member

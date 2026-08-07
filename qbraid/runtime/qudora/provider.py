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
Module defining QUDORA session and provider classes

"""

import os
from typing import Any, Optional

import pyqasm
from pyqasm.exceptions import PyQasmError, QasmParsingError
from qbraid_core.sessions import Session

from qbraid._caching import cached_method
from qbraid._version import __version__ as qbraid_version
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import QudoraDevice

DEFAULT_BASE_URL = "https://api.qudora.com"


def _validate_qasm(program: str) -> None:
    """Validate an OpenQASM program with pyqasm before it is submitted to QUDORA.

    Used as the ``validate`` hook on the device's ``qasm2``/``qasm3`` program specs, so a
    malformed or semantically invalid circuit is rejected during ``device.run()`` rather than
    being sent to the QUDORA server. Raises ``ValueError`` so the qBraid validation pipeline
    surfaces it as a ``ProgramValidationError``.
    """
    try:
        pyqasm.loads(program).validate()
    except (PyQasmError, QasmParsingError) as err:
        raise ValueError(f"Invalid OpenQASM program for QUDORA: {err}") from err


class QudoraSession(Session):
    """Session for the QUDORA Cloud REST API."""

    def __init__(self, token: Optional[str] = None, *, base_url: Optional[str] = None):
        token = token or os.getenv("QUDORA_API_TOKEN")
        if not token:
            raise ValueError(
                "A QUDORA API token is required to initialize the session. "
                "Please provide it directly as an argument or set it via "
                "the QUDORA_API_TOKEN environment variable."
            )

        base_url = base_url or os.getenv("QUDORA_BASE_URL") or DEFAULT_BASE_URL
        super().__init__(
            base_url=base_url.rstrip("/"),
            headers={"Content-Type": "application/json"},
            auth_headers={"Authorization": f"Bearer {token}"},
        )
        self.token = token
        self.add_user_agent(f"QbraidSDK/{qbraid_version}")
        # Retry transient connection drops (e.g. a server-closed keep-alive during status
        # polling) and 5xx responses with backoff, rather than surfacing them as job failures.
        self.initialize_retry()

    def get_backends(self) -> list[dict[str, Any]]:
        """Return all QUDORA backends."""
        return self.get("/backends/").json()

    def get_backend_status(self, backend_id: int) -> str:
        """Return the ``BackendStatusName`` for a single backend."""
        return self.get(f"/backends/status/{backend_id}").json()

    def create_job(self, data: dict[str, Any]) -> int:
        """Create a new job on the QUDORA Cloud and return its integer job id."""
        return self.post("/jobs/", json=data).json()

    def get_job(self, job_id: int | str, *, include_results: bool = False) -> dict[str, Any]:
        """Return the record for a single QUDORA job.

        The QUDORA jobs endpoint is a filtered list (``GET /jobs/?job_id=``) that returns an
        array; an empty array means the job id does not exist.
        """
        params = {
            "job_id": job_id,
            "include_results": include_results,
            "include_input_data": False,
            "include_user_error": True,
        }
        jobs = self.get("/jobs/", params=params).json()
        if not jobs:
            raise ResourceNotFoundError(f"Job '{job_id}' not found.")
        return jobs[0]

    def cancel_job(self, job_id: int | str) -> None:
        """Cancel a QUDORA job by updating its status to ``Canceled``."""
        self.put("/jobs/", params={"job_id": job_id, "status_name": "Canceled"})


class QudoraProvider(QuantumProvider):
    """QUDORA provider class."""

    def __init__(self, token: Optional[str] = None, *, base_url: Optional[str] = None):
        self.session = QudoraSession(token, base_url=base_url)

    def _build_profile(self, backend: dict[str, Any]) -> TargetProfile:
        """Build a profile for a QUDORA backend.

        The ``device_id`` is the backend ``username`` because that is the value the QUDORA
        submit endpoint expects in the job ``target`` field.
        """
        return TargetProfile(
            device_id=backend["username"],
            # Both currently published QUDORA backends are simulators. The backend record does
            # not expose a confirmed hardware/simulator flag (see plans/qudora/qudora-sdk.md).
            simulator=True,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=backend["max_n_qubits"],
            program_spec=[
                ProgramSpec(str, alias="qasm2", validate=_validate_qasm),
                ProgramSpec(str, alias="qasm3", validate=_validate_qasm),
            ],
            provider_name="QUDORA",
            qudora_full_name=backend["full_name"],
            max_shots=backend["max_shots"],
            max_programs_per_job=backend["max_programs_per_job"],
            user_settings_schema=backend["user_settings_schema"],
            # Optional: only used by the (id-based) backend status endpoint.
            qudora_backend_id=backend.get("id"),
        )

    @cached_method
    def get_device(self, device_id: str) -> QudoraDevice:
        """Return a single QUDORA device by its ``username`` device id."""
        for backend in self.session.get_backends():
            if backend["username"] == device_id:
                return QudoraDevice(self._build_profile(backend), self.session)
        raise ResourceNotFoundError(f"Device '{device_id}' not found.")

    @cached_method
    def get_devices(self) -> list[QudoraDevice]:
        """Return all QUDORA devices."""
        return [
            QudoraDevice(self._build_profile(backend), self.session)
            for backend in self.session.get_backends()
        ]

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(self, "_hash", hash((self.session.token, self.session.base_url)))
        return self._hash  # pylint: disable=no-member

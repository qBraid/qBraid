# Copyright 2026 qBraid
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
Module defining AQT session and provider classes.

Authentication tokens are obtained through ``aqt-connector`` (OIDC via Auth0); all job I/O
(device discovery, submission, polling, cancellation) is performed by :class:`AQTSession`
against the AQT arnica REST API directly. Circuit conversion to the AQT native basis is
handled by the device's ``ProgramSpec`` serialize hook (:func:`qiskit_to_aqt`).

"""

from __future__ import annotations

import os
from typing import Any, Optional

from qbraid_core._import import LazyLoader
from qbraid_core.sessions import Session

from qbraid._caching import cached_method
from qbraid._version import __version__ as qbraid_version
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .converter import qiskit_to_aqt
from .device import AQTDevice

qiskit = LazyLoader("qiskit", globals(), "qiskit")

DEFAULT_ARNICA_URL = "https://arnica.aqt.eu/api"


def _resolve_access_token(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    """Resolve a bearer access token for the AQT arnica API (no explicit token given).

    Resolution order (non-interactive by design — never triggers the device/QR flow):
    ``AQT_ACCESS_TOKEN`` env → a token from ``aqt-connector`` (a stored/refreshed session token,
    or the client-credentials flow). ``client_id`` / ``client_secret`` default to the
    ``AQT_CLIENT_ID`` / ``AQT_CLIENT_SECRET`` env vars when not passed explicitly. ``audience``
    (the arnica API root, e.g. staging vs production) aligns the OIDC token request and the
    token verifier with the target deployment.

    Raises:
        ValueError: If no token can be resolved without interactive login.
    """
    token = os.getenv("AQT_ACCESS_TOKEN")
    if token:
        return token

    client_id = client_id or os.getenv("AQT_CLIENT_ID")
    client_secret = client_secret or os.getenv("AQT_CLIENT_SECRET")

    try:
        # pylint: disable-next=import-outside-toplevel
        from aqt_connector import ArnicaApp, ArnicaConfig, get_access_token, log_in
    except ImportError as err:  # pragma: no cover - exercised only without the aqt extra
        raise ValueError(
            "AQT authentication requires the 'aqt-connector' package. Install the AQT extra "
            "with `pip install qbraid[aqt]`, or pass an access_token / set AQT_ACCESS_TOKEN."
        ) from err

    config = ArnicaConfig()
    # Never persist tokens to disk: aqt-connector otherwise writes to ``~/.aqt/access_token``
    # (and crashes if the directory is absent), which is wrong for a stateless/containerized
    # deployment (e.g. Cloud Run). The token is held in memory by ``AQTSession`` and re-minted
    # via the client-credentials flow on demand.
    config.store_access_token = False
    if client_id is not None:
        config.client_id = client_id
    if client_secret is not None:
        config.client_secret = client_secret
    if audience:
        # aqt-connector pins the OIDC audience to production and never overrides it from the
        # environment/config file. The client-credentials grant must *request* this audience
        # (config.oidc_config.audience), and the returned token is *verified* against
        # config.arnica_url, so align both with the target arnica API root (prod vs staging).
        config.arnica_url = audience
        config.oidc_config.audience = audience

    app = ArnicaApp(config)

    token = get_access_token(app)
    if token:
        return token

    if config.client_id and config.client_secret:
        # Non-interactive machine-to-machine (client-credentials) grant.
        return log_in(app)

    raise ValueError(
        "No AQT access token available. Provide one of: an access_token argument, the "
        "AQT_ACCESS_TOKEN env var, AQT_CLIENT_ID/AQT_CLIENT_SECRET for the client-credentials "
        "flow, or an interactive session via `python -m aqt_connector log-in`."
    )


class AQTSession(Session):
    """HTTP session for the AQT arnica REST API (v1)."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        *,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        arnica_url: Optional[str] = None,
    ):
        api_url = (arnica_url or os.getenv("AQT_ARNICA_URL") or DEFAULT_ARNICA_URL).rstrip("/")

        if api_url.endswith("/v1"):
            api_url = api_url[: -len("/v1")].rstrip("/")

        # The OIDC audience must match the arnica API root (staging vs production), so resolve
        # the token only after the deployment URL is known.
        token = access_token or _resolve_access_token(
            client_id=client_id, client_secret=client_secret, audience=api_url
        )

        super().__init__(
            base_url=f"{api_url}/v1",
            headers={"Content-Type": "application/json"},
            auth_headers={"Authorization": f"Bearer {token}"},
        )
        self._access_token = token
        self.add_user_agent(f"QbraidSDK/{qbraid_version}")

    @property
    def access_token(self) -> str:
        """Return the bearer access token used by this session."""
        return self._access_token

    def get_workspaces(self) -> list[dict[str, Any]]:
        """List the workspaces (and their resources) visible to the token."""
        return self.get("/workspaces").json()

    def get_resource(self, resource_id: str) -> dict[str, Any]:
        """Return the details (status, available qubits, characterization) of a resource."""
        try:
            return self.get(f"/resources/{resource_id}").json()
        except Exception as err:  # pylint: disable=broad-except
            raise ResourceNotFoundError(f"Resource '{resource_id}' not found.") from err

    def submit_job(
        self, workspace_id: str, resource_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        """Submit a ``quantum_circuit`` job to a workspace/resource."""
        return self.post(f"/submit/{workspace_id}/{resource_id}", json=body).json()

    def get_result(self, job_id: str, include_timing_data: bool = False) -> dict[str, Any]:
        """Return the current state (and result, if finished) of a job."""
        params = {"include_timing_data": str(include_timing_data).lower()}
        return self.get(f"/result/{job_id}", params=params).json()

    def cancel_job(self, job_id: str) -> None:
        """Cancel a queued or ongoing job."""
        self.delete(f"/jobs/{job_id}")


class AQTProvider(QuantumProvider):
    """AQT (Alpine Quantum Technologies) provider class."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        *,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        arnica_url: Optional[str] = None,
    ):
        self.session = AQTSession(
            access_token,
            client_id=client_id,
            client_secret=client_secret,
            arnica_url=arnica_url,
        )

    @staticmethod
    def _build_profile(resource: dict[str, Any], workspace_id: str) -> TargetProfile:
        """Build a :class:`TargetProfile` from an arnica resource description."""
        resource_id = resource["id"]
        resource_type = resource.get("type", "")
        return TargetProfile(
            device_id=f"{workspace_id}/{resource_id}",
            simulator=resource_type == "simulator",
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=resource.get("available_qubits"),
            # Target qiskit: the transpiler routes any supported program to a qiskit circuit,
            # then the serialize hook converts it to the AQT native-basis payload.
            program_spec=ProgramSpec(
                qiskit.QuantumCircuit, alias="qiskit", serialize=qiskit_to_aqt
            ),
            provider_name="AQT",
            # Extras (accessible via ``device.profile.<key>``): arnica routing + metadata.
            aqt_workspace_id=workspace_id,
            aqt_resource_id=resource_id,
            aqt_resource_type=resource_type,
        )

    @cached_method
    def get_devices(self, **kwargs) -> list[AQTDevice]:  # pylint: disable=unused-argument
        """Get a list of available AQT devices across all visible workspaces."""
        devices: list[AQTDevice] = []
        for workspace in self.session.get_workspaces():
            workspace_id = workspace["id"]
            for resource in workspace.get("resources", []):
                details = self.session.get_resource(resource["id"])
                details.setdefault("id", resource["id"])
                details.setdefault("type", resource.get("type", ""))
                devices.append(AQTDevice(self._build_profile(details, workspace_id), self.session))
        return devices

    @cached_method
    def get_device(self, device_id: str) -> AQTDevice:
        """Get a specific AQT device by ``"<workspace_id>/<resource_id>"`` id."""
        workspace_id, separator, resource_id = device_id.partition("/")
        if not separator:
            raise ResourceNotFoundError(
                f"Invalid AQT device id '{device_id}'. Expected '<workspace_id>/<resource_id>'."
            )
        details = self.session.get_resource(resource_id)
        details.setdefault("id", resource_id)
        return AQTDevice(self._build_profile(details, workspace_id), self.session)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(
                self, "_hash", hash((self.session.access_token, self.session.base_url))
            )
        return self._hash  # pylint: disable=no-member

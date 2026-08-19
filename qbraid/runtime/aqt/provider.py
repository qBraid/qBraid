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
handled by the ``qiskit -> aqt_connector`` transpiler edge (:func:`qiskit_to_aqt_connector`).

"""

from __future__ import annotations

import os
from typing import Any

from aqt_connector import ArnicaApp, ArnicaConfig, get_access_token, log_in
from aqt_connector.models.arnica.resources import ResourceType
from aqt_connector.models.arnica.response_bodies.jobs import ResultResponse, SubmitJobResponse
from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails
from aqt_connector.models.arnica.response_bodies.workspaces import Workspace
from aqt_connector.models.circuits import QuantumCircuit as AQTQuantumCircuit
from qbraid_core.exceptions import RequestsApiError
from qbraid_core.sessions import Session

from qbraid._caching import cached_method
from qbraid._version import __version__ as qbraid_version
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import AQTDevice

DEFAULT_ARNICA_URL = "https://arnica.aqt.eu/api"


def _resolve_access_token(
    client_id: str | None = None,
    client_secret: str | None = None,
    audience: str | None = None,
) -> str:
    """Resolve a bearer access token for the AQT arnica API (no explicit token given).

    Resolution order (non-interactive by design — never triggers the device/QR flow): a token from
    ``aqt-connector`` (a stored/refreshed session token, else the client-credentials flow).
    ``client_id`` / ``client_secret`` default to the ``AQT_CLIENT_ID`` / ``AQT_CLIENT_SECRET`` env
    vars when not passed explicitly. ``audience`` (the arnica API root, e.g. staging vs production)
    aligns the OIDC token request and the token verifier with the target deployment.

    A pre-obtained token can instead be supplied via the ``access_token`` argument of
    :class:`AQTProvider` / :class:`AQTSession`, or the ``AQT_ACCESS_TOKEN`` env var (both bypass
    this function).

    Raises:
        ValueError: If no token can be resolved without interactive login.
    """
    client_id = client_id or os.getenv("AQT_CLIENT_ID")
    client_secret = client_secret or os.getenv("AQT_CLIENT_SECRET")

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
        access_token: str | None = None,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        arnica_url: str | None = None,
    ):
        api_url = (arnica_url or os.getenv("AQT_ARNICA_URL") or DEFAULT_ARNICA_URL).rstrip("/")

        if api_url.endswith("/v1"):
            api_url = api_url[: -len("/v1")].rstrip("/")

        # The OIDC audience must match the arnica API root (staging vs production), so resolve
        # the token only after the deployment URL is known.
        token = (
            access_token
            or os.getenv("AQT_ACCESS_TOKEN")
            or _resolve_access_token(
                client_id=client_id, client_secret=client_secret, audience=api_url
            )
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

    def get_workspaces(self) -> list[Workspace]:
        """List the workspaces (and their resources) visible to the token."""
        return [Workspace.model_validate(item) for item in self.get("/workspaces").json()]

    def get_resource(self, resource_id: str) -> ResourceDetails:
        """Return the details (status, available qubits, characterisation) of a resource."""
        try:
            return ResourceDetails.model_validate(self.get(f"/resources/{resource_id}").json())
        except RequestsApiError as err:
            # Only a genuine 404 means "no such resource"; let auth (401/403), server, and network
            # errors propagate instead of masking every failure as not-found.
            response = getattr(err.__cause__, "response", None)
            if getattr(response, "status_code", None) == 404:
                raise ResourceNotFoundError(f"Resource '{resource_id}' not found.") from err
            raise

    def submit_job(
        self, workspace_id: str, resource_id: str, body: dict[str, Any]
    ) -> SubmitJobResponse:
        """Submit a ``quantum_circuit`` job to a workspace/resource."""
        return SubmitJobResponse.model_validate(
            self.post(f"/submit/{workspace_id}/{resource_id}", json=body).json()
        )

    def get_result(self, job_id: str, include_timing_data: bool = False) -> ResultResponse:
        """Return the current state (and result, if finished) of a job.

        ``GET /result/{job_id}`` is arnica's canonical job-state endpoint (there is no separate
        status endpoint); it returns the full result only once the job has finished.
        """
        params = {"include_timing_data": str(include_timing_data).lower()}
        return ResultResponse.model_validate(self.get(f"/result/{job_id}", params=params).json())

    def cancel_job(self, job_id: str) -> None:
        """Cancel a queued or ongoing job."""
        self.delete(f"/jobs/{job_id}")


class AQTProvider(QuantumProvider):
    """AQT (Alpine Quantum Technologies) provider class."""

    def __init__(
        self,
        access_token: str | None = None,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        arnica_url: str | None = None,
    ):
        self.session = AQTSession(
            access_token,
            client_id=client_id,
            client_secret=client_secret,
            arnica_url=arnica_url,
        )

    @staticmethod
    def _build_profile(resource: ResourceDetails, workspace_id: str) -> TargetProfile:
        """Build a :class:`TargetProfile` from a validated arnica resource description.

        Every field read here is required by ``ResourceDetails``, so a malformed arnica payload
        fails at ``model_validate`` in :meth:`AQTSession.get_resource` rather than silently
        yielding a profile with a missing qubit count or a device mislabelled as a simulator.
        """
        return TargetProfile(
            device_id=f"{workspace_id}/{resource.id}",
            simulator=resource.type is ResourceType.SIMULATOR,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=resource.available_qubits,
            # Target the native "aqt_connector" program type (alias derived from the package): the
            # transpiler routes any supported program to a qiskit circuit and then to the AQT
            # native circuit via the qiskit -> aqt_connector edge.
            program_spec=ProgramSpec(AQTQuantumCircuit),
            provider_name="AQT",
            # Extras (accessible via ``device.profile.<key>``): arnica routing + metadata.
            aqt_workspace_id=workspace_id,
            aqt_resource_id=resource.id,
            aqt_resource_type=resource.type.value,
        )

    @cached_method
    def get_devices(self) -> list[AQTDevice]:
        """Get a list of available AQT devices across all visible workspaces."""
        devices: list[AQTDevice] = []
        for workspace in self.session.get_workspaces():
            for resource in workspace.resources:
                details = self.session.get_resource(resource.id)
                devices.append(AQTDevice(self._build_profile(details, workspace.id), self.session))
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
        return AQTDevice(self._build_profile(details, workspace_id), self.session)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(
                self, "_hash", hash((self.session.access_token, self.session.base_url))
            )
        return self._hash  # pylint: disable=no-member

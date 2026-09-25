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

import base64
import binascii
import hashlib
import json
import os
import threading
import time
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

# Mint a replacement this long before the cached token expires, so a request already in flight
# is not sent with a token that lapses on the way.
_TOKEN_REFRESH_MARGIN_SECONDS = 300

# Resolved tokens, shared across every session in the process and keyed on the credentials and
# audience that minted them. AQT meters token issuance per client: resolving per session meant a
# caller that builds a session per request minted a token per request, and exhausted the quota.
_TOKEN_CACHE: dict[tuple[str, str, str | None], tuple[str, float]] = {}

# One lock per cache key. Holding a key's lock through its mint makes concurrent misses on that
# key share a single mint, while a slow mint for one set of credentials never blocks a cache hit
# for another.
_TOKEN_LOCKS: dict[tuple[str, str, str | None], threading.Lock] = {}
_TOKEN_LOCKS_GUARD = threading.Lock()


def _token_cache_key(
    client_id: str, client_secret: str, audience: str | None
) -> tuple[str, str, str | None]:
    """Key the cache on a digest of the secret, so the secret itself is never held as a key."""
    return client_id, hashlib.sha256(client_secret.encode()).hexdigest(), audience


def _token_lock(key: tuple[str, str, str | None]) -> threading.Lock:
    """Return the lock guarding ``key``, creating it on first use."""
    with _TOKEN_LOCKS_GUARD:
        return _TOKEN_LOCKS.setdefault(key, threading.Lock())


def _store_access_token(key: tuple[str, str, str | None], token: str) -> str:
    """Cache ``token`` under ``key`` when its expiry can be read, and return it."""
    expiry = _token_expiry(token)
    if expiry is None:
        _TOKEN_CACHE.pop(key, None)
    else:
        _TOKEN_CACHE[key] = (token, expiry)
    return token


def _token_expiry(token: str) -> float | None:
    """Return the ``exp`` claim of a JWT access token, or None when it cannot be read.

    The signature is deliberately not verified: the token was just issued to us over TLS, and
    ``exp`` only decides when to mint a replacement. ``aqt-connector``'s verifier would re-fetch
    the issuer's JWKS on every call, trading one network round trip for another.
    """
    try:
        segment = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
        exp = claims["exp"]
    except (IndexError, KeyError, TypeError, ValueError, binascii.Error):
        return None
    return float(exp) if isinstance(exp, (int, float)) else None


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

    With client credentials given as arguments or env vars, the token is reused across the process
    until :data:`_TOKEN_REFRESH_MARGIN_SECONDS` before its ``exp``; one whose expiry cannot be read
    is returned but never cached. Credentials that aqt-connector finds on its own (its config
    file, or a stored interactive session) are not cached: either can change under a running
    process without changing the key.

    A pre-obtained token can instead be supplied via the ``access_token`` argument of
    :class:`AQTProvider` / :class:`AQTSession`, or the ``AQT_ACCESS_TOKEN`` env var (both bypass
    this function).

    Raises:
        ValueError: If no token can be resolved without interactive login.
    """
    client_id = client_id or os.getenv("AQT_CLIENT_ID")
    client_secret = client_secret or os.getenv("AQT_CLIENT_SECRET")
    if not (client_id and client_secret):
        return _mint_access_token(client_id, client_secret, audience)

    key = _token_cache_key(client_id, client_secret, audience)
    with _token_lock(key):
        cached = _TOKEN_CACHE.get(key)
        if cached is not None and time.time() < cached[1] - _TOKEN_REFRESH_MARGIN_SECONDS:
            return cached[0]
        return _store_access_token(key, _mint_access_token(client_id, client_secret, audience))


def _replace_rejected_token(
    client_id: str | None, client_secret: str | None, audience: str | None, rejected: str
) -> str:
    """Return a token to retry with after ``rejected`` drew a 401.

    A replacement is minted only while the cache still holds ``rejected``: a burst of requests that
    all failed on one revoked token mints once, and the rest retry with that replacement instead of
    each spending a mint. The mint skips aqt-connector's stored token, which may be the very token
    that was rejected.
    """
    client_id = client_id or os.getenv("AQT_CLIENT_ID")
    client_secret = client_secret or os.getenv("AQT_CLIENT_SECRET")
    if not (client_id and client_secret):
        return _mint_access_token(client_id, client_secret, audience, bypass_stored=True)

    key = _token_cache_key(client_id, client_secret, audience)
    with _token_lock(key):
        cached = _TOKEN_CACHE.get(key)
        if cached is not None and cached[0] != rejected:
            return cached[0]
        token = _mint_access_token(client_id, client_secret, audience, bypass_stored=True)
        return _store_access_token(key, token)


def _mint_access_token(
    client_id: str | None,
    client_secret: str | None,
    audience: str | None,
    *,
    bypass_stored: bool = False,
) -> str:
    """Obtain a fresh token from ``aqt-connector``; see :func:`_resolve_access_token`.

    ``bypass_stored`` goes straight to the client-credentials grant when credentials are available,
    for use after a 401: both ``get_access_token`` and ``log_in`` return a stored token first,
    which may be the one the server just rejected.
    """
    config = ArnicaConfig()
    # Never persist tokens to disk: aqt-connector otherwise writes to ``~/.aqt/access_token``
    # (and crashes if the directory is absent), which is wrong for a stateless/containerized
    # deployment (e.g. Cloud Run). Reuse is handled in memory by ``_resolve_access_token``.
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
    resolved_id, resolved_secret = config.client_id, config.client_secret

    if bypass_stored and resolved_id and resolved_secret:
        return app.oidc_service.authenticate_with_client_credentials((resolved_id, resolved_secret))

    token = get_access_token(app)
    if token:
        return token

    if resolved_id and resolved_secret:
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
        # the token only after the deployment URL is known. Only a resolved token can be renewed;
        # an explicit or env-var token is used as given.
        credentials: dict[str, str | None] | None = None
        token = access_token or os.getenv("AQT_ACCESS_TOKEN")
        if not token:
            credentials = {
                "client_id": client_id,
                "client_secret": client_secret,
                "audience": api_url,
            }
            token = _resolve_access_token(**credentials)

        super().__init__(
            base_url=f"{api_url}/v1",
            headers={"Content-Type": "application/json"},
            auth_headers={"Authorization": f"Bearer {token}"},
        )
        self._credentials = credentials
        self._access_token = token
        self.add_user_agent(f"QbraidSDK/{qbraid_version}")

    @property
    def access_token(self) -> str:
        """Return the bearer access token used by this session."""
        return self._access_token

    def _set_access_token(self, token: str) -> None:
        """Send ``token`` from now on, and keep masking it in error messages."""
        self._access_token = token
        self.auth_headers["Authorization"] = f"Bearer {token}"
        self.headers["Authorization"] = f"Bearer {token}"

    def request(self, method: str, url: str | bytes, *args: Any, **kwargs: Any):
        """Send a request, renewing a resolved token that is near expiry or was rejected.

        A session outlives its token, and the header is set once at construction, so the token is
        re-resolved before each request (a cache hit unless it is close to expiry). A 401 on a
        resolved token means it was revoked early, so the request is retried once with a
        replacement. Retrying is safe because a 401 means the request was never processed.
        """
        if self._credentials is None:
            return super().request(method, url, *args, **kwargs)

        token = _resolve_access_token(**self._credentials)
        try:
            return self._send_with(token, method, url, *args, **kwargs)
        except RequestsApiError as err:
            response = getattr(err.__cause__, "response", None)
            if getattr(response, "status_code", None) != 401:
                raise
            token = _replace_rejected_token(rejected=token, **self._credentials)
            return self._send_with(token, method, url, *args, **kwargs)

    def _send_with(self, token: str, method: str, url: str | bytes, *args: Any, **kwargs: Any):
        """Send one request bearing ``token`` as its own header, not the session's.

        Another thread may renew this session's token while the request is in flight; binding the
        token to the request keeps ``token`` exactly what was sent, so a 401 names the right one.
        """
        self._set_access_token(token)
        headers = dict(kwargs.pop("headers", None) or {})
        headers["Authorization"] = f"Bearer {token}"
        return super().request(method, url, *args, headers=headers, **kwargs)

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

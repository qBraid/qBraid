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
Module defining Pasqal provider class.

"""

from __future__ import annotations

import os
import threading
import time
from typing import TYPE_CHECKING, Any

from qbraid_core.sessions import Session

from qbraid._caching import cached_method
from qbraid._logging import logger
from qbraid._version import __version__ as qbraid_version
from qbraid.programs import QPROGRAM_REGISTRY, ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import QbraidRuntimeError, ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import PasqalDevice
from .job import _warn_sdk_renamed

if TYPE_CHECKING:
    from pasqal_cloud.authentication import TokenProvider

    from .device import PasqalClient


class PasqalProviderError(QbraidRuntimeError):
    """Exception raised by :class:`PasqalProvider`."""


class PasqalSession(Session):
    """Session for Pasqal Cloud's device catalog.

    ``pasqal-cloud`` exposes device *specs* but not device *status*, so the
    catalog (status and atom count) is read from ``GET /api/v1/devices``
    directly. The endpoint is public; requests go through this session for its
    connection pooling and retry policy.

    The catalog is cached for :attr:`CACHE_TTL_SECONDS`, so listing every
    device and reading each one's status costs one request rather than one per
    device. A failed fetch is remembered for :attr:`FAILURE_TTL_SECONDS`, so
    callers waiting on the lock during an outage re-raise it instead of each
    repeating the request. ``qbraid.cache_disabled`` does not bypass this cache.
    """

    CACHE_TTL_SECONDS = 30.0
    FAILURE_TTL_SECONDS = 5.0
    # Read timeouts are retried, so a hung catalog costs about four of these.
    REQUEST_TIMEOUT_SECONDS = 10.0

    def __init__(self, core_url: str):
        super().__init__(base_url=core_url.rstrip("/"))
        self.add_user_agent(f"QbraidSDK/{qbraid_version}")
        self.initialize_retry()
        self._cache_lock = threading.Lock()
        self._cached_records: dict[str, dict[str, Any]] | None = None
        self._cached_at = 0.0
        # The last fetch failure; a fresh error is raised from it each time, so a
        # shared exception object does not accumulate tracebacks across callers.
        self._failure: Exception | None = None
        self._failed_at = 0.0

    def get_device_records(self) -> dict[str, dict[str, Any]]:
        """Return Pasqal's device catalog keyed by device type (e.g. ``"EMU_MPS"``).

        A record without a ``device_type`` is skipped with a warning rather than
        failing the whole catalog.

        Returns:
            A copy of the catalog; changing it does not change the cache.

        Raises:
            PasqalProviderError: If the catalog cannot be fetched or parsed.
        """
        with self._cache_lock:
            now = time.monotonic()
            if self._cached_records is not None and now - self._cached_at < self.CACHE_TTL_SECONDS:
                return dict(self._cached_records)
            if self._failure is not None and now - self._failed_at < self.FAILURE_TTL_SECONDS:
                raise PasqalProviderError(
                    f"Failed to fetch the Pasqal device catalog: {self._failure}"
                ) from self._failure

            try:
                response = self.get(
                    f"{self.base_url}/api/v1/devices", timeout=self.REQUEST_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                records = response.json()["data"]
                catalog: dict[str, dict[str, Any]] = {}
                for record in records:
                    device_type = record.get("device_type") if isinstance(record, dict) else None
                    if not device_type:
                        logger.warning("Skipping Pasqal catalog record without a device_type.")
                        continue
                    catalog[device_type] = record
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._failure = exc
                self._failed_at = time.monotonic()
                raise PasqalProviderError(
                    f"Failed to fetch the Pasqal device catalog: {exc}"
                ) from exc

            self._cached_records = catalog
            self._cached_at = time.monotonic()
            self._failure = None
            return dict(catalog)


def _core_url(client: PasqalClient) -> str:
    """Return the core API URL the Pasqal client talks to.

    Reading it off the client keeps the catalog in the same region and
    environment as batch submission (e.g. ``region="sa"``).
    """
    # pylint: disable-next=import-outside-toplevel
    from pasqal_cloud.endpoints import CORE_API_URL

    endpoints = getattr(getattr(client, "_client", None), "endpoints", None)
    return getattr(endpoints, "core", None) or CORE_API_URL


def _device_type_names() -> list[str]:
    """Return every device type Pasqal Cloud accepts for batch submission."""
    # pylint: disable-next=import-outside-toplevel
    from pasqal_cloud.device import DeviceTypeName

    return [member.value for member in DeviceTypeName]


def _build_profile(device_id: str, record: dict[str, Any] | None = None) -> TargetProfile:
    """Build a :class:`TargetProfile` for a Pasqal device.

    Args:
        device_id: Pasqal device identifier (e.g. ``"FRESNEL"``, ``"EMU_FREE"``).
        record: The device's entry in Pasqal's catalog, when it is listed.
            Supplies the maximum atom count. ``None`` for a device type
            Pasqal accepts but does not currently list.

    Returns:
        A :class:`TargetProfile` describing the device for the qBraid runtime.
    """
    sequence_type = QPROGRAM_REGISTRY.get("pulser")
    if sequence_type is None:
        # pylint: disable-next=import-outside-toplevel
        from pulser import Sequence as sequence_type  # type: ignore[assignment]

    program_spec = ProgramSpec(
        sequence_type,
        alias="pulser",
        serialize=lambda sequence: sequence.to_abstract_repr(),
    )
    record = record or {}
    simulator = record.get("is_emulator")
    if not isinstance(simulator, bool):
        simulator = device_id.startswith("EMU_")
    num_qubits = record.get("max_atom_num")
    if isinstance(num_qubits, bool):
        num_qubits = None
    return TargetProfile(
        device_id=device_id,
        simulator=simulator,
        experiment_type=ExperimentType.ANALOG,
        num_qubits=num_qubits if isinstance(num_qubits, int) else None,
        program_spec=program_spec,
        provider_name="pasqal",
    )


def _create_client(
    username: str | None,
    password: str | None,
    project_id: str | None,
    token_provider: TokenProvider | None,
) -> PasqalClient:
    """Construct the ``pasqal-cloud`` client.

    ``pasqal-cloud`` 0.23 added ``PasqalCloudClient`` and deprecated ``SDK``
    in its favour; 0.21 and 0.22 only have ``SDK``.
    """
    try:
        # pylint: disable-next=import-outside-toplevel
        from pasqal_cloud.pasqal_cloud_client import PasqalCloudClient as client_cls
    except ImportError:  # pasqal-cloud 0.21 - 0.22
        # pylint: disable-next=import-outside-toplevel
        from pasqal_cloud import SDK as client_cls  # type: ignore[assignment,no-redef]

    return client_cls(
        username=username,
        password=password,
        token_provider=token_provider,
        project_id=project_id,
    )


class PasqalProvider(QuantumProvider):
    """Implements qBraid's :class:`QuantumProvider` interface for Pasqal Cloud Services.
    Authentication mirrors the ``pasqal_cloud`` client constructor: provide a
    ``username`` / ``password`` pair, a ``token_provider``, or set the
    ``PASQAL_USERNAME``, ``PASQAL_PASSWORD``, and ``PASQAL_PROJECT_ID``
    environment variables.

    Example:

        >>> from qbraid.runtime.pasqal import PasqalProvider
        >>> provider = PasqalProvider(
        ...     username="me@example.com",
        ...     password="...",
        ...     project_id="...",
        ... )
        >>> device = provider.get_device("EMU_FREE")
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        username: str | None = None,
        password: str | None = None,
        project_id: str | None = None,
        token_provider: TokenProvider | None = None,
        client: PasqalClient | None = None,
        *,
        sdk: PasqalClient | None = None,
    ):
        """Initialize the Pasqal provider.

        Args:
            username: Pasqal Cloud Services account username. Falls back to the
                ``PASQAL_USERNAME`` environment variable.
            password: Pasqal Cloud Services password. Falls back to the
                ``PASQAL_PASSWORD`` environment variable. If left unset and a
                ``username`` is provided, ``pasqal-cloud`` will prompt
                interactively.
            project_id: Pasqal project ID under which batches are submitted.
                Falls back to the ``PASQAL_PROJECT_ID`` environment variable.
            token_provider: Custom :class:`pasqal_cloud.TokenProvider` for
                machine-to-machine or pre-issued-token authentication. Takes
                precedence over username/password when supplied.
            client: Pre-built ``pasqal_cloud`` client (``PasqalCloudClient`` or
                the older ``SDK``). When provided, all other authentication
                arguments are ignored. Useful for testing and advanced setups.
            sdk: Deprecated alias for ``client``.

        Raises:
            ValueError: If no authentication material can be resolved.
        """
        if sdk is not None:
            _warn_sdk_renamed("PasqalProvider")
            client = client if client is not None else sdk
        if client is not None:
            self._client = client
        else:
            # An unset CI secret exports as "", which must read as absent rather than be
            # forwarded to the SDK as an empty credential.
            resolved_project_id = project_id or os.getenv("PASQAL_PROJECT_ID") or None
            resolved_username = username or os.getenv("PASQAL_USERNAME") or None
            resolved_password = password or os.getenv("PASQAL_PASSWORD") or None

            if token_provider is None and not resolved_username:
                raise ValueError(
                    "Pasqal authentication is required. Provide a `username` (and"
                    " optionally a `password`), a `token_provider`, or set the"
                    " PASQAL_USERNAME / PASQAL_PASSWORD environment variables."
                )

            self._client = _create_client(
                resolved_username, resolved_password, resolved_project_id, token_provider
            )
        self._session = PasqalSession(_core_url(self._client))

    @property
    def client(self) -> PasqalClient:
        """Return the underlying ``pasqal_cloud`` client."""
        return self._client

    @property
    def sdk(self) -> PasqalClient:
        """Deprecated alias for :attr:`client`."""
        _warn_sdk_renamed("PasqalProvider")
        return self._client

    @property
    def session(self) -> PasqalSession:
        """Return the session used to read Pasqal's device catalog."""
        return self._session

    def _make_device(self, device_id: str, record: dict[str, Any] | None) -> PasqalDevice:
        """Build a :class:`PasqalDevice` sharing this provider's client and session."""
        return PasqalDevice(
            profile=_build_profile(device_id, record), client=self._client, session=self._session
        )

    @cached_method
    def get_devices(self) -> list[PasqalDevice]:
        """Return every Pasqal device type, with limits from Pasqal's live catalog.

        Device types Pasqal accepts but does not currently list (for example
        a QPU in maintenance) are included; their :meth:`PasqalDevice.status`
        reports them as offline.

        Raises:
            PasqalProviderError: If the device catalog cannot be fetched.
        """
        records = self._session.get_device_records()
        device_ids = sorted(set(_device_type_names()) | set(records))
        return [self._make_device(device_id, records.get(device_id)) for device_id in device_ids]

    @cached_method
    def get_device(self, device_id: str) -> PasqalDevice:
        """Return a :class:`PasqalDevice` for the given device identifier.

        If the device catalog cannot be fetched, a device type ``pasqal-cloud``
        accepts is still returned, without its atom count, since submission does
        not use the catalog; its :meth:`~PasqalDevice.status` raises until the
        catalog is back.

        Args:
            device_id: Pasqal device identifier (case-insensitive). Common
                values include ``"FRESNEL"`` (QPU), ``"EMU_FREE"``,
                ``"EMU_TN"``, ``"EMU_FRESNEL"``, ``"EMU_MPS"``, and ``"EMU_SV"``.

        Raises:
            ResourceNotFoundError: If Pasqal Cloud neither lists nor accepts
                the device identifier.
        """
        normalized = device_id.strip().upper()
        try:
            records = self._session.get_device_records()
        except PasqalProviderError as exc:
            logger.warning("Using Pasqal's known device types without the catalog: %s", exc)
            records = {}
        known = set(_device_type_names()) | set(records)
        if normalized not in known:
            raise ResourceNotFoundError(
                f"Device '{device_id}' not found in Pasqal Cloud. "
                f"Available devices: {sorted(known)}"
            )
        return self._make_device(normalized, records.get(normalized))

    def __hash__(self) -> int:
        # The SDK holds credentials and a session; pasqal_cloud objects are not
        # hashable, so we key on the project_id plus instance identity.
        return hash(("pasqal", getattr(self._client, "project_id", None), id(self._client)))

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
from typing import TYPE_CHECKING

from qbraid._caching import cached_method
from qbraid._logging import logger
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import PasqalDevice

if TYPE_CHECKING:
    from pasqal_cloud import SDK as PasqalSDK
    from pasqal_cloud.authentication import TokenProvider


# Default device IDs exposed by Pasqal Cloud. Mirrors
# ``pasqal_cloud.device.DeviceTypeName``; kept here as a literal so we don't
# need to import ``pasqal_cloud`` to enumerate devices ahead of authentication.
_DEFAULT_DEVICE_IDS: tuple[str, ...] = (
    "FRESNEL",
    "FRESNEL_CAN1",
    "EMU_FREE",
    "EMU_TN",
    "EMU_FRESNEL",
    "EMU_MPS",
    "EMU_SV",
)


def _is_simulator(device_id: str) -> bool:
    """Return ``True`` for emulator-style device IDs (``EMU_*``)."""
    return device_id.upper().startswith("EMU_")


def _build_profile(device_id: str, num_qubits: int | None = None) -> TargetProfile:
    """Build a :class:`TargetProfile` for a Pasqal device.

    Args:
        device_id: Pasqal device identifier (e.g. ``"FRESNEL"``, ``"EMU_FREE"``).
        num_qubits: Optional max-qubit count, when known. Pasqal exposes device
            constraints through ``SDK.get_device_specs_dict``; the value is
            stored on the profile as additional metadata under
            ``device_specs`` when provided by the caller.

    Returns:
        A :class:`TargetProfile` describing the device for the qBraid runtime.
    """
    # pylint: disable-next=import-outside-toplevel
    from pulser import Sequence

    return TargetProfile(
        device_id=device_id,
        simulator=_is_simulator(device_id),
        experiment_type=ExperimentType.ANALOG,
        num_qubits=num_qubits,
        program_spec=ProgramSpec(
            Sequence,
            alias="pulser",
            serialize=lambda sequence: sequence.to_abstract_repr(),
        ),
        provider_name="pasqal",
    )


class PasqalProvider(QuantumProvider):
    """Implements qBraid's :class:`QuantumProvider` interface for Pasqal Cloud Services.

    Authentication mirrors the ``pasqal_cloud.SDK`` constructor: provide a
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
        sdk: PasqalSDK | None = None,
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
            sdk: Pre-built ``pasqal_cloud.SDK`` instance. When provided, all
                other authentication arguments are ignored. Useful for testing
                and advanced setups.

        Raises:
            ValueError: If no authentication material can be resolved.
        """
        if sdk is not None:
            self._sdk = sdk
            return

        # pylint: disable-next=import-outside-toplevel
        from pasqal_cloud import SDK

        resolved_project_id = project_id or os.getenv("PASQAL_PROJECT_ID")
        resolved_username = username or os.getenv("PASQAL_USERNAME")
        resolved_password = password or os.getenv("PASQAL_PASSWORD")

        if token_provider is None and not resolved_username:
            raise ValueError(
                "Pasqal authentication is required. Provide a `username` (and"
                " optionally a `password`), a `token_provider`, or set the"
                " PASQAL_USERNAME / PASQAL_PASSWORD environment variables."
            )

        self._sdk = SDK(
            username=resolved_username,
            password=resolved_password,
            token_provider=token_provider,
            project_id=resolved_project_id,
        )

    @property
    def sdk(self) -> PasqalSDK:
        """Return the underlying :class:`pasqal_cloud.SDK` instance."""
        return self._sdk

    def _device_specs(self) -> dict[str, str]:
        """Return Pasqal device specs, swallowing transport errors.

        ``get_device_specs_dict`` may require authentication, so we degrade
        gracefully and return an empty dict on failure -- callers can still
        instantiate emulator devices without it.
        """
        try:
            return self._sdk.get_device_specs_dict()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Could not fetch Pasqal device specs: %s", exc)
            return {}

    @cached_method
    def get_devices(self) -> list[PasqalDevice]:
        """Return the list of Pasqal devices currently available to the caller.

        Falls back to a static enumeration of well-known device IDs when the
        cloud spec endpoint is unreachable, so users can still build emulator
        runs offline.
        """
        specs = self._device_specs()
        if not specs:
            return []
        device_ids: tuple[str, ...] = tuple(specs.keys())
        return [
            PasqalDevice(profile=_build_profile(device_id), sdk=self._sdk)
            for device_id in device_ids
        ]

    @cached_method
    def get_device(self, device_id: str) -> PasqalDevice:
        """Return a :class:`PasqalDevice` for the given device identifier.

        Args:
            device_id: Pasqal device identifier (case-insensitive). Common
                values include ``"FRESNEL"`` (QPU), ``"EMU_FREE"``,
                ``"EMU_TN"``, ``"EMU_FRESNEL"``, ``"EMU_MPS"``, and ``"EMU_SV"``.

        Raises:
            ResourceNotFoundError: If the device identifier is not recognised
                by Pasqal Cloud and is not one of the well-known defaults.
        """
        normalized = device_id.strip().upper()
        specs = self._device_specs()
        known = set(specs.keys()) | set(_DEFAULT_DEVICE_IDS)
        if normalized not in known:
            raise ResourceNotFoundError(
                f"Device '{device_id}' not found in Pasqal Cloud. "
                f"Available devices: {sorted(known)}"
            )
        return PasqalDevice(profile=_build_profile(normalized), sdk=self._sdk)

    def __hash__(self) -> int:
        # The SDK holds credentials and a session; pasqal_cloud objects are not
        # hashable, so we key on the project_id plus instance identity.
        return hash(("pasqal", getattr(self._sdk, "project_id", None), id(self._sdk)))

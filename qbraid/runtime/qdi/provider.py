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
Module defining the QDI provider class

"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import pyqasm
from pyqasm.exceptions import PyQasmError, QasmParsingError

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .client import QdiHttpClient, resolve_qdi_client
from .device import QdiDevice
from .exceptions import QdiError, qdi_call
from .protocol import QdiClient, QdiDeviceDescriptor, QdiStatus

# QDI task types are vendor-declared strings; these are the ones that map onto
# a qBraid program spec today. Anything else is carried in the profile only.
TASK_TYPE_ALIASES: dict[str, str] = {
    "openqasm3": "qasm3",
    "qasm3": "qasm3",
    "openqasm2": "qasm2",
    "qasm2": "qasm2",
}


def _validate_qasm(program: str) -> None:
    """Reject a malformed OpenQASM program before it is sent to the device."""
    try:
        pyqasm.loads(program).validate()
    except (PyQasmError, QasmParsingError) as err:
        raise ValueError(f"Invalid OpenQASM program for QDI device: {err}") from err


class QdiProvider(QuantumProvider):
    """Provider for any device reachable through the Quantum Device Interface.

    The provider is transport-agnostic: give it a ``client`` implementing
    :class:`~qbraid.runtime.qdi.QdiClient` (an instance, a ``qbraid.qdi_clients``
    entry-point name, or a ``"module:Class"`` path), or give it a ``base_url``
    to talk QDI over HTTP. ``credentials`` is the dict handed to the client's
    ``authenticate`` call; its keys are whatever the device's auth method needs.
    """

    def __init__(
        self,
        client: QdiClient | str | None = None,
        *,
        credentials: Mapping[str, Any] | None = None,
        base_url: str | None = None,
        token: str | None = None,
    ):
        if client is None:
            base_url = base_url or os.getenv("QDI_BASE_URL")
            if not base_url:
                raise ValueError(
                    "A QDI client is required. Pass a client implementing the QDI surface, "
                    "or a base_url (or set QDI_BASE_URL) to connect over HTTP."
                )
            client = QdiHttpClient(base_url, token=token or os.getenv("QDI_API_TOKEN"))
        elif base_url or token:
            raise ValueError("base_url and token only apply when no client is given.")
        elif isinstance(client, str):
            client = resolve_qdi_client(client)
        elif not isinstance(client, QdiClient):
            raise TypeError(
                f"{type(client).__name__} does not implement the QDI client surface "
                "(discover/authenticate/send/monitor/receive/estimate_resources)."
            )

        self._client: QdiClient = client
        self._credentials = dict(credentials) if credentials else None
        self._authenticated = False

    @property
    def client(self) -> QdiClient:
        """Return the underlying QDI client."""
        return self._client

    def _discover(self) -> list[QdiDeviceDescriptor]:
        with qdi_call("discover"):
            response = self._client.discover()
        return [QdiDeviceDescriptor.from_dict(entry) for entry in response["devices"]]

    def discover(self) -> list[QdiDeviceDescriptor]:
        """Run the QDI handshake and return the device descriptors.

        Spec §2.2 makes Discover the one operation that needs no credentials,
        so it is tried first and its result used to pick the ``device_id`` for
        Authenticate. A device that rejects an unauthenticated Discover
        (OQTOPUS does) gets authenticated first and discovered second, so both
        call orders work without the provider knowing which vendor it holds.
        """
        if self._authenticated or self._credentials is None:
            return self._discover()

        try:
            descriptors: list[QdiDeviceDescriptor] | None = self._discover()
        except QdiError as err:
            if err.status != QdiStatus.ERROR_UNAUTHORIZED:
                raise
            descriptors = None

        device_id = descriptors[0].device_id if descriptors else ""
        with qdi_call("authenticate"):
            self._client.authenticate(device_id, self._credentials)
        self._authenticated = True
        return descriptors if descriptors is not None else self._discover()

    def _build_profile(self, descriptor: QdiDeviceDescriptor) -> TargetProfile:
        aliases: list[str] = []
        for task_type in descriptor.supported_task_types:
            alias = TASK_TYPE_ALIASES.get(task_type)
            if alias and alias not in aliases:
                aliases.append(alias)
        program_spec = [ProgramSpec(str, alias=alias, validate=_validate_qasm) for alias in aliases]

        # The descriptor has no device-type field; honor one if a vendor adds it.
        extra = descriptor.extra
        simulator = bool(extra.get("simulator")) or extra.get("device_type") == "simulator"

        # TargetProfile allows extra keys, but its synthesized __init__ only names the
        # declared fields; passing the QDI ones as a mapping keeps mypy happy.
        extras: dict[str, Any] = {
            "display_name": descriptor.display_name,
            "supported_task_types": list(descriptor.supported_task_types),
            "supported_extensions": list(descriptor.supported_extensions),
            "supported_auth_methods": list(descriptor.supported_auth_methods),
            "supports_estimation": descriptor.supports_estimation,
        }
        return TargetProfile(
            device_id=descriptor.device_id,
            simulator=simulator,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=descriptor.num_qubits,
            program_spec=program_spec or None,
            provider_name="QDI",
            **extras,
        )

    @cached_method
    def get_devices(self) -> list[QdiDevice]:  # type: ignore[override]
        """Return every device the QDI connection discovers."""
        return [
            QdiDevice(self._build_profile(descriptor), self._client)
            for descriptor in self.discover()
        ]

    @cached_method
    def get_device(self, device_id: str) -> QdiDevice:
        """Return a single discovered device by its ``device_id``."""
        for descriptor in self.discover():
            if descriptor.device_id == device_id:
                return QdiDevice(self._build_profile(descriptor), self._client)
        raise ResourceNotFoundError(f"Device '{device_id}' not found.")

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(self, "_hash", hash((type(self), id(self._client))))
        return self._hash  # pylint: disable=no-member

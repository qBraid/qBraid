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
The Quantum Device Interface (QDI) v0.2 client surface: status codes, task
states, the device descriptor, and the structural ``QdiClient`` protocol that
any transport (in-process vendor adapter or QDI-over-HTTP) must satisfy.

Kept free of qBraid runtime imports so it can be lifted into a neutral
reference package once the working group publishes one.

"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Protocol, runtime_checkable


class QdiStatus(IntEnum):
    """QDI operation return codes (``qdi_status`` in qdi.h)."""

    SUCCESS = 0
    ERROR_INVALID_ARGUMENT = 1
    ERROR_UNAUTHORIZED = 2
    ERROR_CONNECTION_FAILED = 3
    ERROR_TASK_NOT_FOUND = 4
    ERROR_UNSUPPORTED_FORMAT = 5
    ERROR_HARDWARE_FAULT = 6
    ERROR_ESTIMATION_FAILED = 7
    ERROR_UNKNOWN = 99


class QdiTaskStatus(IntEnum):
    """QDI task execution states (``qdi_task_status`` in qdi.h, spec §3.3)."""

    QUEUED = 0
    EXECUTING = 1
    COMPLETED = 2
    FAULTED = 3
    CANCELLED = 4


@dataclass(frozen=True)
class QdiDeviceDescriptor:
    """One entry of a QDI ``discover()`` response (spec §3.1).

    Every field the spec marks as required is indexed directly by
    :meth:`from_dict`, so a descriptor missing one fails at parse time.
    Keys the spec does not define are preserved in ``extra``.
    """

    device_id: str
    supported_auth_methods: tuple[str, ...]
    supported_task_types: tuple[str, ...]
    supported_extensions: tuple[str, ...]
    is_ready: bool
    supports_estimation: bool
    num_qubits: int | None
    display_name: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    _FIELDS = (
        "device_id",
        "supported_auth_methods",
        "supported_task_types",
        "supported_extensions",
        "is_ready",
        "supports_estimation",
        "num_qubits",
        "display_name",
    )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> QdiDeviceDescriptor:
        """Build a descriptor from the JSON-compatible dict a client returns."""
        return cls(
            device_id=data["device_id"],
            supported_auth_methods=tuple(data["supported_auth_methods"]),
            supported_task_types=tuple(data["supported_task_types"]),
            supported_extensions=tuple(data["supported_extensions"]),
            is_ready=bool(data["is_ready"]),
            supports_estimation=bool(data["supports_estimation"]),
            num_qubits=data["num_qubits"],
            display_name=data.get("display_name"),
            extra={key: value for key, value in data.items() if key not in cls._FIELDS},
        )


@runtime_checkable
class QdiClient(Protocol):
    """Structural type of a QDI v0.2 client.

    Signatures match qdi-demo's ``NativeQdiClient`` and qdi-oqtopus's
    ``OqtopusQdiClient``. Implementations report failures by raising; the
    exception should expose an integer ``status`` (or ``code``) attribute
    holding a :class:`QdiStatus` value so it can be translated faithfully.
    """

    def discover(self) -> dict:
        """Return ``{"devices": [<descriptor dict>, ...]}``."""
        ...  # pylint: disable=unnecessary-ellipsis

    def authenticate(self, device_id: str, credentials_dict: dict) -> None:
        """Establish trust using the device's declared auth method."""
        ...  # pylint: disable=unnecessary-ellipsis

    def send(
        self,
        device_id: str,
        task_payload: bytes,
        task_type: str,
        shots: int = 100,
        extensions: dict[str, Any] | None = None,
    ) -> str:
        """Submit an opaque task and return the device task id."""
        ...  # pylint: disable=unnecessary-ellipsis

    def monitor(self, device_id: str, task_id: str) -> tuple[int, dict]:
        """Return ``(QdiTaskStatus value, advisory metadata)``."""
        ...  # pylint: disable=unnecessary-ellipsis

    def receive(self, device_id: str, task_id: str) -> tuple[str, str]:
        """Return ``(result payload, result_type)`` for a completed task."""
        ...  # pylint: disable=unnecessary-ellipsis

    def estimate_resources(
        self,
        device_id: str,
        task_payload: bytes,
        task_type: str,
        shots: int = 100,
        extensions: dict[str, Any] | None = None,
    ) -> dict:
        """Dry-run a task and return the device's resource estimate."""
        ...  # pylint: disable=unnecessary-ellipsis

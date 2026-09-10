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
QDI-over-HTTP client and vendor client resolution.

"""

from __future__ import annotations

import importlib
import json
from typing import Any

from qbraid_core.exceptions import RequestsApiError
from qbraid_core.sessions import Session

from qbraid._entrypoints import load_entrypoint
from qbraid._version import __version__ as qbraid_version

from .exceptions import QdiError
from .protocol import QdiClient, QdiStatus, QdiTaskStatus

# QDI does not standardize its HTTP binding yet; this is the one served by
# the working group's reference server (shassinger/qdi-demo).
DEFAULT_API_PREFIX = "/qdi/v1"

_HTTP_STATUS_TO_QDI: dict[int, QdiStatus] = {
    400: QdiStatus.ERROR_INVALID_ARGUMENT,
    401: QdiStatus.ERROR_UNAUTHORIZED,
    403: QdiStatus.ERROR_UNAUTHORIZED,
    404: QdiStatus.ERROR_TASK_NOT_FOUND,
    422: QdiStatus.ERROR_INVALID_ARGUMENT,
    501: QdiStatus.ERROR_ESTIMATION_FAILED,
}

_QDI_METHODS = ("discover", "authenticate", "send", "monitor", "receive", "estimate_resources")


class QdiHttpClient:
    """:class:`~qbraid.runtime.qdi.QdiClient` over the QDI REST binding.

    A ``token`` given up front is sent as a bearer token on every request,
    which spec §2.2 allows in place of the ``authenticate`` handshake. Calling
    :meth:`authenticate` instead stores the ``access_token`` the server returns.

    Wraps a :class:`qbraid_core.sessions.Session` rather than subclassing it:
    the QDI verb ``send`` would otherwise shadow ``requests.Session.send``,
    which ``request`` calls internally.
    """

    def __init__(
        self, base_url: str, token: str | None = None, *, api_prefix: str = DEFAULT_API_PREFIX
    ):
        self.session = Session(
            base_url=base_url.rstrip("/"),
            headers={"Content-Type": "application/json"},
            auth_headers={"Authorization": f"Bearer {token}"} if token else None,
        )
        self.token = token
        self._base_url = base_url.rstrip("/")
        self._prefix = "/" + api_prefix.strip("/")
        self.session.add_user_agent(f"QbraidSDK/{qbraid_version}")
        self.session.initialize_retry()

    @property
    def base_url(self) -> str:
        """Return the endpoint the client talks to."""
        return self._base_url

    @property
    def headers(self) -> dict[str, Any]:
        """Return the headers sent on every request, including the bearer token."""
        return dict(self.session.headers)

    def _set_token(self, token: str) -> None:
        self.token = token
        self.session.auth_headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(self.session.auth_headers)

    def _device_path(self, device_id: str, *parts: str) -> str:
        return "/".join([self._prefix, "devices", device_id, *parts])

    def _call(self, operation: str, method: str, path: str, **kwargs) -> Any:
        try:
            return self.session.request(method, path, **kwargs).json()
        except RequestsApiError as err:
            status_code = err.status_code
            if status_code is None:
                status = QdiStatus.ERROR_CONNECTION_FAILED
            else:
                status = _HTTP_STATUS_TO_QDI.get(status_code, QdiStatus.ERROR_UNKNOWN)
            raise QdiError(status, str(err), operation=operation) from err

    @staticmethod
    def _task_body(
        task_payload: bytes, task_type: str, shots: int, extensions: dict[str, Any] | None
    ) -> dict[str, Any]:
        # The reference binding carries the payload as a JSON string, so it
        # must be text. Binary formats will need a base64 rule in the binding.
        try:
            payload = task_payload.decode("utf-8")
        except UnicodeDecodeError as err:
            raise QdiError(
                QdiStatus.ERROR_UNSUPPORTED_FORMAT,
                "The QDI HTTP binding only carries UTF-8 text payloads.",
                operation="send",
            ) from err
        return {
            "task_payload": payload,
            "task_type": task_type,
            "shots": shots,
            "extensions": extensions or {},
        }

    def discover(self) -> dict:
        """Return the device list from ``GET /devices``."""
        return self._call("discover", "GET", f"{self._prefix}/devices")

    def authenticate(self, device_id: str, credentials_dict: dict) -> None:
        """Exchange credentials for a bearer token via ``POST /devices/{id}/authenticate``."""
        response = self._call(
            "authenticate",
            "POST",
            self._device_path(device_id, "authenticate"),
            json=credentials_dict,
        )
        self._set_token(response["access_token"])

    def send(
        self,
        device_id: str,
        task_payload: bytes,
        task_type: str,
        shots: int = 100,
        extensions: dict[str, Any] | None = None,
    ) -> str:
        """Submit a task via ``POST /devices/{id}/tasks`` and return its id."""
        response = self._call(
            "send",
            "POST",
            self._device_path(device_id, "tasks"),
            json=self._task_body(task_payload, task_type, shots, extensions),
        )
        return response["task_id"]

    def monitor(self, device_id: str, task_id: str) -> tuple[int, dict]:
        """Poll ``GET /devices/{id}/tasks/{task_id}/status``."""
        response = self._call(
            "monitor", "GET", self._device_path(device_id, "tasks", task_id, "status")
        )
        name = response["status"]
        try:
            status = QdiTaskStatus[name]
        except KeyError as err:
            raise QdiError(
                QdiStatus.ERROR_UNKNOWN,
                f"Server reported task status '{name}', which is not a QDI state.",
                operation="monitor",
            ) from err
        return int(status), response.get("advisory_metadata") or {}

    def receive(self, device_id: str, task_id: str) -> tuple[str, str]:
        """Fetch ``GET /devices/{id}/tasks/{task_id}/results`` as ``(payload, result_type)``."""
        response = self._call(
            "receive", "GET", self._device_path(device_id, "tasks", task_id, "results")
        )
        return json.dumps(response["result"]), response["result_type"]

    def estimate_resources(
        self,
        device_id: str,
        task_payload: bytes,
        task_type: str,
        shots: int = 100,
        extensions: dict[str, Any] | None = None,
    ) -> dict:
        """Dry-run a task via ``POST /devices/{id}/estimate``."""
        return self._call(
            "estimate_resources",
            "POST",
            self._device_path(device_id, "estimate"),
            json=self._task_body(task_payload, task_type, shots, extensions),
        )


def resolve_qdi_client(spec: str) -> QdiClient:
    """Instantiate a vendor QDI client named by entry point or import path.

    ``spec`` is first looked up in the ``qbraid.qdi_clients`` entry-point group,
    which a vendor package populates with one line in its ``pyproject.toml``::

        [project.entry-points."qbraid.qdi_clients"]
        oqtopus = "qdi_oqtopus.client:OqtopusQdiClient"

    Failing that it is treated as ``"package.module:ClassName"`` (or
    ``"package.module.ClassName"``). The class is instantiated with no
    arguments; pass a ready-made instance to ``QdiProvider`` when it needs some.
    """
    try:
        client_class = load_entrypoint("qdi_clients", spec)
    except Exception:  # pylint: disable=broad-exception-caught
        client_class = None

    if client_class is None:
        module_name, sep, attr = spec.partition(":")
        if not sep:
            module_name, _, attr = spec.rpartition(".")
        if not module_name or not attr:
            raise ValueError(
                f"'{spec}' is neither a registered 'qbraid.qdi_clients' entry point nor an "
                "import path of the form 'package.module:ClassName'."
            )
        try:
            client_class = getattr(importlib.import_module(module_name), attr)
        except (ImportError, AttributeError) as err:
            raise ValueError(f"Could not import QDI client '{spec}': {err}") from err

    if not all(callable(getattr(client_class, name, None)) for name in _QDI_METHODS):
        raise TypeError(
            f"'{spec}' resolved to {client_class!r}, which does not implement the QDI client "
            "surface (discover/authenticate/send/monitor/receive/estimate_resources)."
        )
    try:
        return client_class()
    except TypeError as err:
        raise ValueError(
            f"QDI client '{spec}' could not be constructed without arguments ({err}). "
            "Construct it yourself and pass the instance to QdiProvider."
        ) from err

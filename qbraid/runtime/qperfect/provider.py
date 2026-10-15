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
Module defining QPerfect (MIMIQ) provider class.

The provider holds an authenticated ``MimiqConnection`` and hands it to each device and job.
:mod:`~qbraid.runtime.qperfect.client` resolves the credentials. Circuit conversion runs on the
transpiler's ``qiskit -> mimiqcircuits`` edge.

"""

from __future__ import annotations

import threading

from mimiqcircuits import Circuit as MimiqCircuit
from mimiqcircuits import MimiqConnection

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .client import build_connection
from .device import QPerfectDevice

# The algorithm (auto / statevector / mps) is a per-job option, not a separate device.
_DEVICE_ID = "mimiq-emulator"


class QPerfectProvider(QuantumProvider):
    """QPerfect (MIMIQ) provider class."""

    def __init__(
        self,
        token: str | None = None,
        *,
        url: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        """Build a QPerfect provider.

        Credentials are resolved on first connection use, so constructing a provider never
        raises for missing configuration. See
        :func:`~qbraid.runtime.qperfect.client.build_connection` for the resolution order and
        the environment variables behind each argument.

        Args:
            token: A MIMIQ refresh token.
            url: The MIMIQ cloud URL.
            username: MIMIQ account email.
            password: MIMIQ account password.
        """
        self._token = token
        self._url = url
        self._username = username
        self._password = password
        self._connection: MimiqConnection | None = None
        self._connection_lock = threading.Lock()
        # The refresh token a discarded connection last held. MIMIQ rotates it on every refresh,
        # so after the first 15 minutes the one passed in has stopped working.
        self._latest_token: str | None = None

    @property
    def connection(self) -> MimiqConnection:
        """Return an authenticated MIMIQ connection, establishing it on first use.

        A connection that is no longer open is replaced. mimiqlink's token refresher has no error
        handling, so one failed refresh ends the thread and the connection stays closed for good.
        The lock gives concurrent callers one login: each login starts a refresher thread that
        runs for the life of the process.
        """
        with self._connection_lock:
            if self._connection is None or not self._connection.connection.isOpen():
                if self._connection is not None:
                    self._remember_token(self._connection)
                self._connection = build_connection(
                    self._latest_token or self._token,
                    url=self._url,
                    username=self._username,
                    password=self._password,
                )
            return self._connection

    def invalidate_connection(self, connection: MimiqConnection | None = None) -> None:
        """Discard the connection so the next access logs in again, stopping its refresher.

        For a session MIMIQ no longer accepts while it still reports open. Pass the connection the
        failed call used: if it has already been replaced, nothing happens, so concurrent failures
        on one session cost one login. ``None`` discards whatever connection is current.

        Jobs created on the discarded connection keep it, and its access token expires without
        the refresher.
        """
        with self._connection_lock:
            current = self._connection
            if current is None or (connection is not None and current is not connection):
                return
            self._remember_token(current)
            self._connection = None
        _stop_refresher(current)

    def _remember_token(self, connection: MimiqConnection) -> None:
        """Keep a discarded connection's refresh token for the next login.

        Without it, a provider built from a token alone could not log in again once MIMIQ had
        rotated that token, and would stay disconnected for the life of the process.
        """
        token = getattr(connection.connection, "refresh_token", None)
        if isinstance(token, str) and token:
            self._latest_token = token

    @staticmethod
    def _build_profile() -> TargetProfile:
        """Build the :class:`TargetProfile` for the MIMIQ emulator."""
        return TargetProfile(
            device_id=_DEVICE_ID,
            simulator=True,
            experiment_type=ExperimentType.GATE_MODEL,
            # No cap: MPS reach depends on entanglement, not width, so a fixed count would reject
            # circuits MIMIQ can run. MIMIQ rejects what its chosen backend cannot handle.
            num_qubits=None,
            program_spec=ProgramSpec(MimiqCircuit),
            provider_name="QPerfect",
        )

    @cached_method
    def get_devices(self) -> list[QPerfectDevice]:
        """Get the available QPerfect (MIMIQ) devices (a single cloud emulator)."""
        return [QPerfectDevice(self._build_profile(), self)]

    @cached_method
    def get_device(self, device_id: str) -> QPerfectDevice:
        """Get the QPerfect MIMIQ emulator by its device id (``"mimiq-emulator"``)."""
        if device_id != _DEVICE_ID:
            raise ResourceNotFoundError(
                f"Unknown QPerfect device '{device_id}'. The only device is '{_DEVICE_ID}'."
            )
        return QPerfectDevice(self._build_profile(), self)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(self, "_hash", hash((self._token, self._url, self._username)))
        return self._hash  # pylint: disable=no-member


def _stop_refresher(connection: MimiqConnection) -> None:
    """Ask a discarded connection's token-refresher thread to exit.

    ``close()`` is not used: it joins the refresher, which waits out a token refresh in progress.
    The thread checks the flag every second and is a daemon, so nothing has to join it.
    """
    link = connection.connection
    with link.refresher_lock:
        link.refresher_stop = True

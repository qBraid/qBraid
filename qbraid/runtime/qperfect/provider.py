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

# Approximate reach per backend: state vector is memory-bound (2^N amplitudes), MPS scales with
# entanglement. The emulator errors if a run exceeds what its chosen backend can handle.
_ALGORITHM_QUBITS: dict[str, int] = {
    "statevector": 32,
    "mps": 256,
}


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

    @property
    def connection(self) -> MimiqConnection:
        """Return an authenticated MIMIQ connection, establishing it on first use."""
        if self._connection is None:
            self._connection = build_connection(
                self._token,
                url=self._url,
                username=self._username,
                password=self._password,
            )
        return self._connection

    @staticmethod
    def _build_profile() -> TargetProfile:
        """Build the :class:`TargetProfile` for the MIMIQ emulator."""
        return TargetProfile(
            device_id=_DEVICE_ID,
            simulator=True,
            experiment_type=ExperimentType.GATE_MODEL,
            # The emulator picks a backend per job, so advertise the largest reach.
            num_qubits=max(_ALGORITHM_QUBITS.values()),
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

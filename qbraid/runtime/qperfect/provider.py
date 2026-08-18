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

Authentication and all job I/O are driven through the vendor ``mimiqcircuits`` SDK: the provider
holds an authenticated ``MimiqConnection`` (established from ``QPERFECT_API_TOKEN`` via
``connectToken``) and hands it to each device/job. Circuit conversion to the MIMIQ native circuit is
handled by the transpiler's ``qiskit -> mimiqcircuits`` edge (:func:`qiskit_to_mimiqcircuits`).

"""

from __future__ import annotations

from mimiqcircuits import Circuit as MimiqCircuit
from mimiqcircuits import MimiqConnection

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .client import build_connection, resolve_token
from .device import QPerfectDevice

# MIMIQ exposes a single cloud emulator; the simulation algorithm (auto / statevector / mps) is a
# per-job runtime option, not a separate device.
_DEVICE_ID = "mimiq-emulator"

# Practical qubit reach per MIMIQ backend: state vector is memory-bound (2^N amplitudes); MPS scales
# with entanglement. The emulator auto-selects a backend per job, so the device advertises the
# largest. Approximate — the emulator errors if a run exceeds what its chosen backend can handle.
_ALGORITHM_QUBITS: dict[str, int] = {
    "statevector": 32,
    "mps": 256,
}


class QPerfectProvider(QuantumProvider):
    """QPerfect (MIMIQ) provider class."""

    def __init__(self, token: str | None = None, *, url: str | None = None):
        self._token = resolve_token(token)
        self._url = url
        self._connection: MimiqConnection | None = None

    @property
    def connection(self) -> MimiqConnection:
        """Return an authenticated MIMIQ connection, establishing it on first use."""
        if self._connection is None:
            self._connection = build_connection(self._token, url=self._url)
        return self._connection

    @staticmethod
    def _build_profile() -> TargetProfile:
        """Build the :class:`TargetProfile` for the MIMIQ emulator."""
        return TargetProfile(
            device_id=_DEVICE_ID,
            simulator=True,
            experiment_type=ExperimentType.GATE_MODEL,
            # The emulator auto-selects a state-vector or MPS backend per job; advertise the largest
            # reach across backends (the algorithm is chosen at submit time via runtime options).
            num_qubits=max(_ALGORITHM_QUBITS.values()),
            # Target the native "mimiqcircuits" program type: the transpiler routes any supported
            # program to a qiskit circuit, then to the MIMIQ native circuit via the
            # qiskit -> mimiqcircuits edge.
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
            object.__setattr__(self, "_hash", hash((self._token, self._url)))
        return self._hash  # pylint: disable=no-member

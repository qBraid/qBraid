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

"""IQM provider, session, and quantum-computer discovery helpers."""

from __future__ import annotations

import os
import platform
from functools import partial
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING
from urllib.parse import urlparse
from uuid import UUID

import requests
from qbraid_core._import import LazyLoader
from qiskit import QuantumCircuit

from qbraid._caching import cached_method
from qbraid._version import __version__ as qbraid_version
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import IQMDevice, to_iqm_circuit

if TYPE_CHECKING:
    import iqm.iqm_client
    import iqm.iqm_server_client.iqm_server_client
    import iqm.station_control.client.authentication

iqm_client = LazyLoader("iqm_client", globals(), "iqm.iqm_client")
iqm_server_client = LazyLoader(
    "iqm_server_client",
    globals(),
    "iqm.iqm_server_client.iqm_server_client",
)
iqm_authentication = LazyLoader(
    "iqm_authentication",
    globals(),
    "iqm.station_control.client.authentication",
)

IQM_SERVER_URL_ENV = "IQM_SERVER_URL"
IQM_QUANTUM_COMPUTER_ENV = "IQM_QUANTUM_COMPUTER"
DEFAULT_IQM_SERVER_URL = "https://resonance.meetiqm.com"


def _create_client_signature(client_signature: str | None) -> str:
    """Build the User-Agent value expected by the IQM server client."""
    signature = platform.platform(terse=True)
    signature += f", python {platform.python_version()}"
    try:
        iqm_client_version = version("iqm-client")
    except PackageNotFoundError:
        iqm_client_version = "unknown"
    signature += f", IQMClient iqm-client {iqm_client_version}"
    if client_signature:
        signature += f", {client_signature}"
    return signature


def _normalize_server_url(iqm_server_url: str) -> str:
    """Validate and normalize an IQM server base URL."""
    if not iqm_server_url.isascii():
        raise iqm_authentication.ClientConfigurationError(
            f"Non-ASCII characters in URL: {iqm_server_url}"
        )
    try:
        url = urlparse(iqm_server_url)
    except Exception as err:  # pragma: no cover - ``urlparse`` is very permissive.
        raise iqm_authentication.ClientConfigurationError(f"Invalid URL: {iqm_server_url}") from err

    if url.scheme not in {"http", "https"}:
        raise iqm_authentication.ClientConfigurationError(
            f"The URL schema has to be http or https. Incorrect schema in URL: {iqm_server_url}"
        )
    if url.hostname is None:
        raise iqm_authentication.ClientConfigurationError(f"Invalid URL: {iqm_server_url}")
    if url.path not in {"", "/"}:
        raise iqm_authentication.ClientConfigurationError(
            "The IQM Server URL must be a server base URL without a quantum computer path."
        )

    port_suffix = f":{url.port}" if url.port else ""
    return f"{url.scheme}://{url.hostname}{port_suffix}"


def list_quantum_computers(
    iqm_server_url: str,
    *,
    token: str | None = None,
    tokens_file: str | None = None,
    client_signature: str | None = None,
) -> tuple[str, ...]:
    """List the quantum-computer aliases visible through an IQM server."""
    root_url = _normalize_server_url(iqm_server_url)
    token_manager = iqm_authentication.TokenManager(token, tokens_file)
    auth_header_callback = token_manager.get_auth_header_callback()
    headers = {
        "User-Agent": _create_client_signature(client_signature),
        "Accept": "application/json",
    }
    if auth_header_callback:
        headers["Authorization"] = auth_header_callback()

    response = requests.get(
        f"{root_url}/api/v1/quantum-computers",
        headers=headers,
        timeout=iqm_server_client.REQUESTS_TIMEOUT,
    )
    if not response.ok:
        try:
            response_json = response.json()
            error_message = response_json.get("message") or response_json["detail"]
        except (ValueError, KeyError):
            error_message = response.text

        error_class = iqm_server_client.map_from_status_code_to_error(response.status_code)
        raise error_class(error_message)

    payload = iqm_server_client.ListQuantumComputersResponse.model_validate_json(response.text)
    return tuple(quantum_computer.alias for quantum_computer in payload.quantum_computers)


class IQMSession:
    """Thin wrapper around the public ``iqm-client`` SDK."""

    def __init__(
        self,
        url: str | None = None,
        *,
        quantum_computer: str | None = None,
        token: str | None = None,
        tokens_file: str | None = None,
        client_signature: str | None = None,
    ):
        resolved_url = (url or os.getenv(IQM_SERVER_URL_ENV) or DEFAULT_IQM_SERVER_URL).rstrip("/")

        self.url = resolved_url
        self.quantum_computer = quantum_computer or os.getenv(IQM_QUANTUM_COMPUTER_ENV)
        self.client_signature = client_signature or f"QbraidSDK/{qbraid_version}"
        self._token = token
        self._tokens_file = tokens_file
        self._client: iqm.iqm_client.IQMClient | None = None
        self._auth_config = {
            "quantum_computer": self.quantum_computer,
            "token": self._token,
            "tokens_file": tokens_file,
        }

    def with_quantum_computer(self, quantum_computer: str) -> IQMSession:
        """Return a session scoped to a specific IQM quantum computer alias."""
        return self.__class__(
            self.url,
            quantum_computer=quantum_computer,
            token=self._token,
            tokens_file=self._tokens_file,
            client_signature=self.client_signature,
        )

    @property
    def client(self) -> iqm.iqm_client.IQMClient:
        """Return the underlying IQM client."""
        if self._client is None:
            self._client = iqm_client.IQMClient(
                self.url,
                quantum_computer=self.quantum_computer,
                token=self._token,
                tokens_file=self._tokens_file,
                client_signature=self.client_signature,
            )
        return self._client

    @staticmethod
    def _coerce_job_id(job_id: str | UUID) -> UUID:
        return job_id if isinstance(job_id, UUID) else UUID(str(job_id))

    def get_static_quantum_architecture(self) -> iqm.iqm_client.StaticQuantumArchitecture:
        """Return the static quantum architecture for the selected quantum computer."""
        return self.client.get_static_quantum_architecture()

    def get_dynamic_quantum_architecture(
        self, calibration_set_id: UUID | None = None
    ) -> iqm.iqm_client.DynamicQuantumArchitecture:
        """Return the dynamic quantum architecture for the selected quantum computer."""
        return self.client.get_dynamic_quantum_architecture(calibration_set_id)

    def submit_circuits(  # pylint: disable=too-many-arguments
        self,
        circuits: iqm.iqm_client.CircuitBatch,
        *,
        qubit_mapping: iqm.iqm_client.QubitMapping | None = None,
        calibration_set_id: UUID | None = None,
        shots: int = 1,
        options: iqm.iqm_client.CircuitCompilationOptions | None = None,
        use_timeslot: bool = False,
    ) -> iqm.iqm_client.CircuitJob:
        """Submit one or more IQM circuits."""
        return self.client.submit_circuits(
            circuits,
            qubit_mapping=qubit_mapping,
            calibration_set_id=calibration_set_id,
            shots=shots,
            options=options,
            use_timeslot=use_timeslot,
        )

    def get_job(self, job_id: str | UUID) -> iqm.iqm_client.CircuitJob:
        """Return the current state of an IQM job."""
        return self.client.get_job(self._coerce_job_id(job_id))

    def get_job_measurements(
        self, job_id: str | UUID
    ) -> iqm.iqm_client.CircuitMeasurementResultsBatch:
        """Return the measurement results for a completed IQM job."""
        return self.client.get_job_measurements(self._coerce_job_id(job_id))

    def cancel_job(self, job_id: str | UUID) -> None:
        """Cancel a submitted job."""
        self.client.cancel_job(self._coerce_job_id(job_id))

    def list_quantum_computers(self) -> tuple[str, ...]:
        """Return the quantum computer aliases visible through the configured account."""
        if self.quantum_computer is not None:
            return (self.quantum_computer,)
        return list_quantum_computers(
            self.url,
            token=self._token,
            tokens_file=self._tokens_file,
            client_signature=self.client_signature,
        )


class IQMProvider(QuantumProvider):
    """IQM provider class."""

    def __init__(
        self,
        url: str | None = None,
        *,
        quantum_computer: str | None = None,
        token: str | None = None,
        tokens_file: str | None = None,
        client_signature: str | None = None,
    ):
        self.session = IQMSession(
            url,
            quantum_computer=quantum_computer,
            token=token,
            tokens_file=tokens_file,
            client_signature=client_signature,
        )

    @staticmethod
    def _build_basis_gates(gates: set[str]) -> list[str]:
        """Map IQM native operations to qiskit-facing basis gates."""
        basis_gates = []
        if "prx" in gates:
            basis_gates.append("r")
        if "cz" in gates:
            basis_gates.append("cz")
        if "move" in gates:
            basis_gates.append("move")
        return basis_gates

    @staticmethod
    def _canonical_qubit_pair(
        first: str,
        second: str,
        qubit_order: dict[str, int],
    ) -> tuple[str, str]:
        return (first, second) if qubit_order[first] <= qubit_order[second] else (second, first)

    @classmethod
    def _build_qubit_connectivity(
        cls,
        static_architecture: iqm.iqm_client.StaticQuantumArchitecture,
        dynamic_architecture: iqm.iqm_client.DynamicQuantumArchitecture,
    ) -> tuple[tuple[str, str], ...]:
        """Build the simplified qubit-only CZ graph used for qiskit transpilation."""
        qubits = tuple(static_architecture.qubits)
        qubit_names = set(qubits)
        resonators = set(static_architecture.computational_resonators)
        qubit_order = {qubit: index for index, qubit in enumerate(qubits)}
        connectivity: set[tuple[str, str]] = set()

        cz_info = dynamic_architecture.gates.get("cz")
        move_info = dynamic_architecture.gates.get("move")
        cz_loci = getattr(cz_info, "loci", ())
        move_loci = getattr(move_info, "loci", ())

        move_by_resonator: dict[str, set[str]] = {}
        for first, second in move_loci:
            if first in qubit_names and second in resonators:
                move_by_resonator.setdefault(second, set()).add(first)

        for first, second in cz_loci:
            if first in qubit_names and second in qubit_names:
                connectivity.add(cls._canonical_qubit_pair(first, second, qubit_order))
                continue

            if first in qubit_names and second in resonators:
                gate_qubit, resonator = first, second
            elif second in qubit_names and first in resonators:
                gate_qubit, resonator = second, first
            else:
                continue

            for move_qubit in move_by_resonator.get(resonator, ()):
                if move_qubit == gate_qubit:
                    continue
                connectivity.add(cls._canonical_qubit_pair(gate_qubit, move_qubit, qubit_order))

        if not connectivity:
            for edge in static_architecture.connectivity:
                if len(edge) != 2 or any(component not in qubit_names for component in edge):
                    continue
                connectivity.add(cls._canonical_qubit_pair(edge[0], edge[1], qubit_order))

        return tuple(
            sorted(
                connectivity,
                key=lambda edge: (qubit_order[edge[0]], qubit_order[edge[1]]),
            )
        )

    def _build_profile(
        self,
        static_architecture: iqm.iqm_client.StaticQuantumArchitecture,
        dynamic_architecture: iqm.iqm_client.DynamicQuantumArchitecture,
        *,
        quantum_computer: str | None,
    ) -> TargetProfile:
        """Build a qBraid target profile from IQM architecture data."""
        native_operations = set(dynamic_architecture.gates.keys())
        device_id = (
            quantum_computer or getattr(static_architecture, "dut_label", None) or self.session.url
        )
        dut_label = getattr(static_architecture, "dut_label", None)
        return TargetProfile(
            device_id=device_id,
            simulator=False,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=len(static_architecture.qubits),
            program_spec=ProgramSpec(
                QuantumCircuit,
                alias="qiskit",
                serialize=partial(
                    to_iqm_circuit,
                    qubit_index_to_name=dict(enumerate(static_architecture.qubits)),
                ),
            ),
            provider_name="IQM",
            basis_gates=self._build_basis_gates(native_operations),
            device_name=dut_label or device_id,
            endpoint_url=self.session.url,
            native_operations=tuple(sorted(native_operations)),
            quantum_computer=quantum_computer,
            dut_label=dut_label,
            qubits=tuple(static_architecture.qubits),
            computational_resonators=tuple(static_architecture.computational_resonators),
            qubit_connectivity=self._build_qubit_connectivity(
                static_architecture,
                dynamic_architecture,
            ),
            calibration_set_id=dynamic_architecture.calibration_set_id,
        )

    def _build_device(self, quantum_computer: str) -> IQMDevice:
        """Build an IQM device bound to a specific quantum computer alias."""
        session = (
            self.session
            if self.session.quantum_computer == quantum_computer
            else self.session.with_quantum_computer(quantum_computer)
        )
        static_architecture = session.get_static_quantum_architecture()
        dynamic_architecture = session.get_dynamic_quantum_architecture()
        profile = self._build_profile(
            static_architecture,
            dynamic_architecture,
            quantum_computer=quantum_computer,
        )
        return IQMDevice(profile=profile, session=session)

    @cached_method
    def get_device(self, device_id: str) -> IQMDevice:
        """Return the IQM device exposed by the configured server."""
        for quantum_computer in self.session.list_quantum_computers():
            device = self._build_device(quantum_computer)
            if device.id == device_id or device.profile.get("dut_label") == device_id:
                return device
        raise ResourceNotFoundError(f"Device '{device_id}' not found.")

    @cached_method
    def get_devices(self, **kwargs) -> list[IQMDevice]:
        """Return the IQM device list for the configured server."""
        device_id = kwargs.get("device_id")
        devices = [
            self._build_device(quantum_computer)
            for quantum_computer in self.session.list_quantum_computers()
        ]
        if device_id is not None:
            return [
                device
                for device in devices
                if device.id == device_id or device.profile.get("dut_label") == device_id
            ]
        return devices

    def __hash__(self):
        if not hasattr(self, "_hash"):
            auth_items = tuple(sorted(self.session._auth_config.items()))
            object.__setattr__(
                self,
                "_hash",
                hash((self.session.url, self.session.client_signature, auth_items)),
            )
        return self._hash  # pylint: disable=no-member

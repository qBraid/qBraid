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

from __future__ import annotations

import os
from typing import Optional
from uuid import UUID

from qiskit import QuantumCircuit

from qbraid._caching import cached_method
from qbraid._version import __version__ as qbraid_version
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from . import _compat
from .device import IQMDevice

IQM_SERVER_URL_ENV = "IQM_SERVER_URL"
IQM_QUANTUM_COMPUTER_ENV = "IQM_QUANTUM_COMPUTER"
DEFAULT_IQM_SERVER_URL = "https://resonance.meetiqm.com"


class IQMSession:
    """Thin wrapper around the public ``iqm-client`` SDK."""

    def __init__(
        self,
        url: Optional[str] = None,
        *,
        quantum_computer: Optional[str] = None,
        token: Optional[str] = None,
        tokens_file: Optional[str] = None,
        client_signature: Optional[str] = None,
    ):
        resolved_url = (url or os.getenv(IQM_SERVER_URL_ENV) or DEFAULT_IQM_SERVER_URL).rstrip("/")

        self.url = resolved_url
        self.quantum_computer = quantum_computer or os.getenv(IQM_QUANTUM_COMPUTER_ENV)
        self.client_signature = client_signature or f"QbraidSDK/{qbraid_version}"
        self._token = token
        self._tokens_file = tokens_file
        self._client = None
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
    def client(self):
        """Return the underlying IQM client."""
        if self._client is None:
            symbols = _compat.load_iqm_symbols()
            self._client = symbols.IQMClient(
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

    def get_static_quantum_architecture(self):
        """Return the static quantum architecture for the selected quantum computer."""
        return self.client.get_static_quantum_architecture()

    def get_dynamic_quantum_architecture(self, calibration_set_id: UUID | None = None):
        """Return the dynamic quantum architecture for the selected quantum computer."""
        return self.client.get_dynamic_quantum_architecture(calibration_set_id)

    def submit_circuits(self, circuits, **kwargs):
        """Submit one or more IQM circuits."""
        return self.client.submit_circuits(circuits, **kwargs)

    def get_job(self, job_id: str | UUID):
        """Return the current state of an IQM job."""
        return self.client.get_job(self._coerce_job_id(job_id))

    def get_job_measurements(self, job_id: str | UUID):
        """Return the measurement results for a completed IQM job."""
        return self.client.get_job_measurements(self._coerce_job_id(job_id))

    def cancel_job(self, job_id: str | UUID) -> None:
        """Cancel a submitted job."""
        self.client.cancel_job(self._coerce_job_id(job_id))

    def list_quantum_computers(self) -> tuple[str, ...]:
        """Return the quantum computer aliases visible through the configured account."""
        if self.quantum_computer is not None:
            return (self.quantum_computer,)
        return _compat.list_quantum_computers(
            self.url,
            token=self._token,
            tokens_file=self._tokens_file,
            client_signature=self.client_signature,
        )


class IQMProvider(QuantumProvider):
    """IQM provider class."""

    def __init__(
        self,
        url: Optional[str] = None,
        *,
        quantum_computer: Optional[str] = None,
        token: Optional[str] = None,
        tokens_file: Optional[str] = None,
        client_signature: Optional[str] = None,
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
        static_architecture,
        dynamic_architecture,
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
        static_architecture,
        dynamic_architecture,
        *,
        quantum_computer: str | None,
    ) -> TargetProfile:
        """Build a qBraid target profile from IQM architecture data."""
        native_operations = set(dynamic_architecture.gates.keys())
        device_id = (
            quantum_computer
            or getattr(static_architecture, "dut_label", None)
            or self.session.url
        )
        dut_label = getattr(static_architecture, "dut_label", None)
        return TargetProfile(
            device_id=device_id,
            simulator=False,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=len(static_architecture.qubits),
            program_spec=ProgramSpec(QuantumCircuit, alias="qiskit"),
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
        devices = [self._build_device(quantum_computer) for quantum_computer in self.session.list_quantum_computers()]
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

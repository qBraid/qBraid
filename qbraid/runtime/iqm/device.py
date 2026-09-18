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

"""IQM device implementation."""

from __future__ import annotations

import importlib.util
import logging
from dataclasses import replace
from typing import TYPE_CHECKING
from uuid import UUID

import rustworkx as rx
from qbraid_core._import import LazyLoader

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.iqm.exceptions import IQMDeviceError

from .job import IQMJob

if TYPE_CHECKING:
    import iqm.iqm_client

    import qbraid.runtime
    import qbraid.runtime.iqm.provider

iqm_client = LazyLoader("iqm_client", globals(), "iqm.iqm_client")

logger = logging.getLogger(__name__)

# IQM's client defaults to one shot; qBraid providers default to 100.
DEFAULT_SHOTS = 100


def _backend_qubit_names(backend) -> dict[int, str]:
    """Map Qiskit qubit indices to IQM component names for ``backend``.

    Not the same as ``enumerate(device.qubits)``: the backend indexes only the
    components it exposes -- Sirius calibrates 16 of its 24 qubits -- and Star
    architectures carry a computational resonator past the last qubit, which MOVE
    instructions address.
    """
    width = (
        backend.target_with_resonators.num_qubits
        if backend.has_resonators()
        else backend.num_qubits
    )
    return {index: backend.index_to_qubit_name(index) for index in range(width)}


_DEVICE_STATUS = {
    "online": DeviceStatus.ONLINE,
    "maintenance": DeviceStatus.UNAVAILABLE,
    "offline": DeviceStatus.OFFLINE,
    "out_of_service": DeviceStatus.OFFLINE,
}


class IQMDevice(QuantumDevice):
    """IQM quantum device interface.

    A device holds one calibration snapshot: the qubits it reports and the
    calibration set its jobs run against are those in effect when the device was
    built. IQM recalibrates, which changes both, so fetch a fresh device from the
    provider rather than holding one across a long-running process.
    """

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        session: qbraid.runtime.iqm.provider.IQMSession,
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> qbraid.runtime.iqm.provider.IQMSession:
        """Return the IQM session."""
        return self._session

    @property
    def qubits(self) -> tuple[str, ...]:
        """Return the architecture qubit labels."""
        return tuple(self.profile.get("qubits", ()))

    @property
    def components(self) -> frozenset[str]:
        """Physical component names: qubits plus any computational resonators."""
        return frozenset(self.qubits) | frozenset(
            self.profile.get("computational_resonators") or ()
        )

    @property
    def qubit_connectivity(self) -> tuple[tuple[str, ...], ...]:
        """Return the architecture connectivity."""
        return tuple(self.profile.get("qubit_connectivity", ()))

    def __str__(self):
        """String representation of the IQMDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the current status of the IQM device.

        Reads ``/health``. ``get_static_quantum_architecture`` is ``@cache``d on
        ``IQMClient`` and the provider already called it to build the profile, so it
        would answer from cache and report ``ONLINE`` forever.

        Raises:
            IQMDeviceError: If IQM reports an operational status qBraid does not map.
        """
        health = self.session.get_health()
        operational_status = str(health["operational_status"]).lower()
        try:
            return _DEVICE_STATUS[operational_status]
        except KeyError as err:
            raise IQMDeviceError(
                f"Unrecognized operational status '{operational_status}' "
                f"for device '{self.id}'."
            ) from err

    def transform(self, run_input: iqm.iqm_client.Circuit) -> iqm.iqm_client.Circuit:
        """Route the circuit onto this device's topology.

        IQM's server does not route: a two-qubit gate on a pair that cannot run CZ is
        rejected at submission. When ``qiskit`` is importable the circuit goes through
        IQM's own ``transpile_to_IQM``, which routes and applies IQM's single-qubit
        optimizations. Without it the circuit is left as-is, which is valid whenever
        its interaction graph already embeds in the topology -- ``qubit_mapping_for``
        raises with a clear message when it does not.
        """
        if not isinstance(run_input, iqm_client.Circuit):
            raise TypeError(
                f"IQMDevice.transform expects an 'iqm.iqm_client.Circuit', got "
                f"'{type(run_input).__name__}'. Did you disable the 'transpile' option?"
            )

        # Checked here rather than left to validate(), which runs after transform:
        # routing an oversized circuit raises a bare qiskit TranspilerError.
        width = len({qubit for op in run_input.instructions for qubit in op.locus})
        if self.num_qubits and width > self.num_qubits:
            raise ValueError(
                f"Number of qubits in the circuit ({width}) exceeds "
                f"the device's capacity ({self.num_qubits})."
            )

        if importlib.util.find_spec("qiskit") is None:
            return run_input
        try:
            return self._route_with_qiskit(run_input)
        except ValueError as err:
            # The round trip goes through Qiskit's measurement-key convention, which
            # only circuits serialized from Qiskit follow. Anything else keeps its
            # placement as-is, which qubit_mapping_for still validates before submit.
            logger.debug("Skipping IQM routing for '%s': %s", self.id, err)
            return run_input

    def _route_with_qiskit(self, circuit: iqm.iqm_client.Circuit) -> iqm.iqm_client.Circuit:
        """Round-trip through Qiskit so IQM's own transpiler can route and optimize."""
        # pylint: disable=import-outside-toplevel
        from iqm.qiskit_iqm import IQMBackend, transpile_to_IQM
        from iqm.qiskit_iqm.qiskit_to_iqm import (
            deserialize_instructions,
            serialize_instructions,
        )
        from qiskit.circuit import QuantumRegister
        from qiskit.transpiler import Layout

        logical = sorted({qubit for op in circuit.instructions for qubit in op.locus})
        name_to_index = {name: index for index, name in enumerate(logical)}
        layout = Layout.generate_trivial_layout(QuantumRegister(len(logical), "q"))

        qiskit_circuit = deserialize_instructions(list(circuit.instructions), name_to_index, layout)
        backend = IQMBackend(self.session.client)
        routed = transpile_to_IQM(qiskit_circuit, backend)
        # transpile_to_IQM chose physical qubits using the device's real topology.
        # Serialize with those physical names so qubit_mapping_for leaves them alone
        # rather than reassigning them by logical order and discarding the layout.
        return iqm_client.Circuit(
            name=routed.name,
            instructions=tuple(serialize_instructions(routed, _backend_qubit_names(backend))),
            metadata=None,
        )

    def _coupling_edges(self) -> set[tuple[str, str]]:
        """Physical qubit pairs that support CZ, both directions."""
        edges: set[tuple[str, str]] = set()
        for edge in self.qubit_connectivity:
            if len(edge) == 2:
                edges.add((edge[0], edge[1]))
                edges.add((edge[1], edge[0]))
        return edges

    def qubit_mapping_for(self, circuit: iqm.iqm_client.Circuit) -> dict[str, str] | None:
        """Bind the circuit's logical qubit names to physical qubits on this device.

        Returns ``None`` when the circuit already uses physical names, matching
        what ``IQMClient.submit_circuits`` expects in that case.

        Raises:
            ValueError: If no placement puts every two-qubit gate on a CZ-capable pair.
        """
        physical = list(self.qubits)
        logical = sorted(
            {qubit for instruction in circuit.instructions for qubit in instruction.locus}
        )
        # Resonators count as physical: a routed Star-architecture circuit addresses
        # them by name in MOVE, and remapping one would make the instruction invalid.
        if not logical or set(logical) <= self.components:
            return None

        interactions = {
            tuple(sorted(instruction.locus))
            for instruction in circuit.instructions
            # MOVE runs between a qubit and a resonator, not over the CZ graph.
            if len(instruction.locus) == 2 and instruction.name != "move"
        }
        edges = self._coupling_edges()

        def valid(assignment: dict[str, str]) -> bool:
            return all((assignment[a], assignment[b]) in edges for a, b in interactions)

        if len(logical) > len(physical):
            raise ValueError(
                f"No placement of {len(logical)} qubits on '{self.id}': the device has "
                f"only {len(physical)}."
            )

        identity = {name: physical[index] for index, name in enumerate(logical)}
        if valid(identity):
            return identity

        graph = rx.PyGraph()
        node_for = {qubit: graph.add_node(qubit) for qubit in physical}
        for first, second in edges:
            if not graph.has_edge(node_for[first], node_for[second]):
                graph.add_edge(node_for[first], node_for[second], None)

        pattern = rx.PyGraph()
        pattern_node = {name: pattern.add_node(name) for name in logical}
        for first, second in interactions:
            pattern.add_edge(pattern_node[first], pattern_node[second], None)

        for mapping in rx.vf2_mapping(graph, pattern, subgraph=True, induced=False):
            assignment = {logical[target]: physical[source] for source, target in mapping.items()}
            if valid(assignment):
                return assignment

        raise ValueError(
            f"No placement of {len(logical)} qubits on '{self.id}' puts every two-qubit "
            "gate on a CZ-capable pair. Route the circuit against the device topology first."
        )

    def _place(self, circuit: iqm.iqm_client.Circuit) -> iqm.iqm_client.Circuit:
        """Return ``circuit`` with its qubit names resolved to physical qubits."""
        mapping = self.qubit_mapping_for(circuit)
        if mapping is None:
            return circuit
        return replace(
            circuit,
            instructions=tuple(
                replace(
                    operation,
                    locus=tuple(mapping.get(qubit, qubit) for qubit in operation.locus),
                )
                for operation in circuit.instructions
            ),
        )

    def _resolve_calibration_set_id(self, calibration_set_id: UUID | None = None) -> UUID | None:
        """Resolve the calibration set to use for a single IQM run."""
        return (
            calibration_set_id
            if calibration_set_id is not None
            else self.profile.get("calibration_set_id")
        )

    # pylint: disable-next=arguments-differ,too-many-arguments
    def submit(
        self,
        run_input: iqm.iqm_client.Circuit | list[iqm.iqm_client.Circuit],
        shots: int = DEFAULT_SHOTS,
        *,
        qubit_mapping: iqm.iqm_client.QubitMapping | None = None,
        calibration_set_id: UUID | None = None,
        options: iqm.iqm_client.CircuitCompilationOptions | None = None,
        use_timeslot: bool = False,
    ) -> IQMJob:
        """Submit one or more IQM circuits to the configured server."""
        circuits = [run_input] if not isinstance(run_input, list) else run_input
        if not circuits:
            raise ValueError("run_input list cannot be empty.")

        empty = [index for index, circuit in enumerate(circuits) if not circuit.instructions]
        if empty:
            raise ValueError(
                f"Circuit(s) at index {', '.join(map(str, empty))} contain no instructions. "
                "IQM requires at least one instruction per circuit."
            )

        resolved_calibration_set_id = self._resolve_calibration_set_id(calibration_set_id)

        if self.profile.get("computational_resonators"):
            # Captured when the profile was built; get_dynamic_quantum_architecture is not
            # cached on IQMClient, so refetching it here would be a round trip per run.
            dynamic_architecture = self.profile.get("dynamic_architecture")
            if dynamic_architecture is None:
                dynamic_architecture = self.session.get_dynamic_quantum_architecture(
                    resolved_calibration_set_id
                )
            circuits = [
                iqm_client.transpile_insert_moves(
                    circuit,
                    dynamic_architecture,
                    existing_moves=iqm_client.ExistingMoveHandlingOptions.KEEP,
                )
                for circuit in circuits
            ]

        if qubit_mapping is None:
            # IQM applies a single qubit_mapping to a whole batch, and circuits in one
            # batch can need different placements (a routed circuit already names
            # physical qubits; an unrouted one does not). Resolving each circuit's
            # placement into its own loci sidesteps that, so batches stay submittable.
            circuits = [self._place(circuit) for circuit in circuits]

        job = self.session.submit_circuits(
            circuits,
            qubit_mapping=qubit_mapping,
            calibration_set_id=resolved_calibration_set_id,
            shots=shots,
            options=options,
            use_timeslot=use_timeslot,
        )
        return IQMJob(
            job_id=str(job.job_id),
            session=self.session,
            device=self,
            job=job,
            shots=shots,
            circuit_count=len(circuits),
        )

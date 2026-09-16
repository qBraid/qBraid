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

from typing import TYPE_CHECKING
from uuid import UUID

import rustworkx as rx
from qbraid_core._import import LazyLoader

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import IQMJob

if TYPE_CHECKING:
    import iqm.iqm_client

    import qbraid.runtime
    import qbraid.runtime.iqm.provider

iqm_client = LazyLoader("iqm_client", globals(), "iqm.iqm_client")


class IQMDevice(QuantumDevice):
    """IQM quantum device interface."""

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
    def qubit_connectivity(self) -> tuple[tuple[str, ...], ...]:
        """Return the architecture connectivity."""
        return tuple(self.profile.get("qubit_connectivity", ()))

    def __str__(self):
        """String representation of the IQMDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the current status of the IQM device."""
        try:
            self.session.get_static_quantum_architecture()
        except Exception:  # pylint: disable=broad-exception-caught
            return DeviceStatus.UNAVAILABLE
        return DeviceStatus.ONLINE

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
        if not logical or set(logical) <= set(physical):
            return None

        interactions = {
            tuple(sorted(instruction.locus))
            for instruction in circuit.instructions
            if len(instruction.locus) == 2
        }
        edges = self._coupling_edges()

        def valid(assignment: dict[str, str]) -> bool:
            return all((assignment[a], assignment[b]) in edges for a, b in interactions)

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

    def _resolve_calibration_set_id(self, calibration_set_id: UUID | None = None) -> UUID | None:
        """Resolve the calibration set to use for a single IQM run."""
        return (
            calibration_set_id
            if calibration_set_id is not None
            else self.profile.get("calibration_set_id")
        )

    @staticmethod
    def _build_compilation_options(  # pylint: disable=too-many-arguments
        compilation_options: iqm.iqm_client.CircuitCompilationOptions | None = None,
        *,
        circuit_compilation_options: iqm.iqm_client.CircuitCompilationOptions | None = None,
        max_circuit_duration_over_t2: float | None = None,
        heralding_mode: iqm.iqm_client.HeraldingMode | None = None,
        move_gate_validation: iqm.iqm_client.MoveGateValidationMode | None = None,
        move_gate_frame_tracking: iqm.iqm_client.MoveGateFrameTrackingMode | None = None,
        active_reset_cycles: int | None = None,
        dd_mode: iqm.iqm_client.DDMode | None = None,
        dd_strategy: iqm.iqm_client.DDStrategy | None = None,
    ) -> iqm.iqm_client.CircuitCompilationOptions | None:
        if compilation_options is not None and circuit_compilation_options is not None:
            raise ValueError(
                "Use either 'compilation_options' or 'circuit_compilation_options', not both."
            )

        resolved_options = compilation_options or circuit_compilation_options
        option_fields = {
            "max_circuit_duration_over_t2": max_circuit_duration_over_t2,
            "heralding_mode": heralding_mode,
            "move_gate_validation": move_gate_validation,
            "move_gate_frame_tracking": move_gate_frame_tracking,
            "active_reset_cycles": active_reset_cycles,
            "dd_mode": dd_mode,
            "dd_strategy": dd_strategy,
        }

        if resolved_options is not None:
            if any(value is not None for value in option_fields.values()):
                raise ValueError(
                    "Use either a compilation options object or individual compilation "
                    "option keyword arguments, not both."
                )
            return resolved_options

        option_kwargs = {key: value for key, value in option_fields.items() if value is not None}
        if not option_kwargs:
            return None

        return iqm_client.CircuitCompilationOptions(**option_kwargs)

    # pylint: disable-next=arguments-differ,too-many-arguments
    def submit(
        self,
        run_input: iqm.iqm_client.Circuit | list[iqm.iqm_client.Circuit],
        shots: int = 1,
        *,
        qubit_mapping: iqm.iqm_client.QubitMapping | None = None,
        calibration_set_id: UUID | None = None,
        compilation_options: iqm.iqm_client.CircuitCompilationOptions | None = None,
        circuit_compilation_options: iqm.iqm_client.CircuitCompilationOptions | None = None,
        use_timeslot: bool = False,
        max_circuit_duration_over_t2: float | None = None,
        heralding_mode: iqm.iqm_client.HeraldingMode | None = None,
        move_gate_validation: iqm.iqm_client.MoveGateValidationMode | None = None,
        move_gate_frame_tracking: iqm.iqm_client.MoveGateFrameTrackingMode | None = None,
        active_reset_cycles: int | None = None,
        dd_mode: iqm.iqm_client.DDMode | None = None,
        dd_strategy: iqm.iqm_client.DDStrategy | None = None,
    ) -> IQMJob:
        """Submit one or more IQM circuits to the configured server."""
        circuits = [run_input] if not isinstance(run_input, list) else run_input
        if not circuits:
            raise ValueError("run_input list cannot be empty.")

        resolved_options = self._build_compilation_options(
            compilation_options,
            circuit_compilation_options=circuit_compilation_options,
            max_circuit_duration_over_t2=max_circuit_duration_over_t2,
            heralding_mode=heralding_mode,
            move_gate_validation=move_gate_validation,
            move_gate_frame_tracking=move_gate_frame_tracking,
            active_reset_cycles=active_reset_cycles,
            dd_mode=dd_mode,
            dd_strategy=dd_strategy,
        )
        resolved_calibration_set_id = self._resolve_calibration_set_id(calibration_set_id)

        if self.profile.get("computational_resonators"):
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
            mappings = {
                frozenset((self.qubit_mapping_for(circuit) or {}).items()) for circuit in circuits
            }
            if len(mappings) > 1:
                raise ValueError(
                    "IQM applies one qubit_mapping to the whole batch, but these circuits "
                    "need different placements. Submit them as separate jobs."
                )
            qubit_mapping = dict(next(iter(mappings))) or None

        job = self.session.submit_circuits(
            circuits,
            qubit_mapping=qubit_mapping,
            calibration_set_id=resolved_calibration_set_id,
            shots=shots,
            options=resolved_options,
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

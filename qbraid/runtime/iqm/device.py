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

from typing import TYPE_CHECKING, Any
from uuid import UUID

from qbraid_core._import import LazyLoader
from qiskit import QuantumCircuit, transpile

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from ._qiskit import serialize_circuit
from .job import IQMJob

if TYPE_CHECKING:
    import iqm.iqm_client

    import qbraid.runtime
    import qbraid.runtime.iqm.provider

iqm_client = LazyLoader("iqm_client", globals(), "iqm.iqm_client")


def to_iqm_circuit(
    circuit: QuantumCircuit,
    *,
    qubit_index_to_name: dict[int, str],
) -> iqm.iqm_client.Circuit:
    """Serialize a qiskit circuit to the circuit model accepted by IQM."""
    return serialize_circuit(
        circuit,
        qubit_index_to_name=qubit_index_to_name,
    )


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

    def _get_coupling_map(self) -> list[list[int]] | None:
        """Convert IQM connectivity into a qiskit integer coupling map."""
        if not self.qubit_connectivity:
            return None

        qubit_to_index = {qubit: index for index, qubit in enumerate(self.qubits)}
        qubit_names = set(self.qubits)
        coupling_map = []
        seen_edges = set()

        for edge in self.qubit_connectivity:
            if len(edge) != 2 or any(component not in qubit_names for component in edge):
                continue

            source, target = edge
            source_index = qubit_to_index[source]
            target_index = qubit_to_index[target]

            for directed_edge in ((source_index, target_index), (target_index, source_index)):
                if directed_edge in seen_edges:
                    continue
                seen_edges.add(directed_edge)
                coupling_map.append(list(directed_edge))

        return coupling_map or None

    def transform(self, run_input: QuantumCircuit) -> QuantumCircuit:
        """Transform the input circuit to IQM-compatible qiskit basis gates."""
        # MOVE is an IQM-native operation but not a standard qiskit basis gate.
        # Existing/inferred MOVE operations are handled on the typed IQM circuit
        # in submit(), after qiskit lowering has finished.
        basis_gates = set(self.profile.basis_gates or {"r", "cz"}) - {"move"}
        transpile_kwargs: dict[str, Any] = {
            "basis_gates": sorted(basis_gates),
            "optimization_level": 0,
            "seed_transpiler": 0,
        }
        coupling_map = self._get_coupling_map()
        if coupling_map is not None:
            transpile_kwargs["coupling_map"] = coupling_map

        return transpile(run_input, **transpile_kwargs)

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

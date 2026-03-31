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

from typing import TYPE_CHECKING, Any, Optional, Union, cast

from qiskit import QuantumCircuit, transpile

from qbraid.programs import ProgramSpec, get_program_type_alias
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from . import _compat
from ._qiskit import serialize_circuit
from .job import IQMJob

if TYPE_CHECKING:
    import qbraid.runtime
    import qbraid.runtime.iqm.provider


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

    def _get_coupling_map(self) -> Optional[list[list[int]]]:
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
        transpile_kwargs: dict[str, Any] = {
            "basis_gates": sorted(self.profile.basis_gates or {"r", "cz"}),
            "optimization_level": 0,
            "seed_transpiler": 0,
        }
        coupling_map = self._get_coupling_map()
        if coupling_map is not None:
            transpile_kwargs["coupling_map"] = coupling_map

        return transpile(run_input, **transpile_kwargs)

    def _resolve_calibration_set_id(self, calibration_set_id=None):
        """Resolve the calibration set to use for a single IQM run."""
        return calibration_set_id if calibration_set_id is not None else self.profile.get(
            "calibration_set_id"
        )

    def prepare(self, run_input: QuantumCircuit, *, calibration_set_id=None) -> Any:
        """Serialize a transpiled qiskit circuit into an IQM circuit."""
        if self._target_spec is None or not self._options.get("prepare"):
            return run_input

        symbols = _compat.load_iqm_symbols()
        resolved_calibration_set_id = self._resolve_calibration_set_id(calibration_set_id)
        qubit_index_to_name = {index: qubit for index, qubit in enumerate(self.qubits)}
        iqm_circuit = serialize_circuit(
            run_input,
            qubit_index_to_name=qubit_index_to_name,
            circuit_cls=symbols.Circuit,
        )
        if not self.profile.get("computational_resonators"):
            return iqm_circuit

        dynamic_architecture = self.session.get_dynamic_quantum_architecture(resolved_calibration_set_id)
        return symbols.transpile_insert_moves(
            iqm_circuit,
            dynamic_architecture,
            existing_moves=symbols.ExistingMoveHandlingOptions.KEEP,
        )

    def apply_runtime_profile(self, run_input: QuantumCircuit, *, calibration_set_id=None) -> Any:
        """Process a qiskit program using a single calibration set across preparation and submission."""
        if self._target_spec is not None and self._options.get("transpile") is True:
            run_input_alias = get_program_type_alias(run_input, safe=True)
            run_input_spec = ProgramSpec(type(run_input), alias=run_input_alias)
            run_input = self.transpile(run_input, run_input_spec)

        is_single_output = not isinstance(run_input, list)
        run_input = [run_input] if is_single_output else run_input

        if self._options.get("transform") is True:
            run_input = [self.transform(p) for p in cast(list, run_input)]

        self.validate(run_input)
        run_input = [
            self.prepare(p, calibration_set_id=calibration_set_id) for p in cast(list, run_input)
        ]

        run_input = run_input[0] if is_single_output else run_input
        return run_input

    @staticmethod
    def _build_compilation_options(
        compilation_options=None,
        *,
        circuit_compilation_options=None,
        max_circuit_duration_over_t2=None,
        heralding_mode=None,
        move_gate_validation=None,
        move_gate_frame_tracking=None,
        active_reset_cycles=None,
        dd_mode=None,
        dd_strategy=None,
    ):
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

        symbols = _compat.load_iqm_symbols()
        return symbols.CircuitCompilationOptions(**option_kwargs)

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input: Union[Any, list[Any]],
        shots: int = 1,
        *,
        qubit_mapping: Optional[dict[str, str]] = None,
        calibration_set_id=None,
        compilation_options=None,
        circuit_compilation_options=None,
        use_timeslot: bool = False,
        max_circuit_duration_over_t2=None,
        heralding_mode=None,
        move_gate_validation=None,
        move_gate_frame_tracking=None,
        active_reset_cycles=None,
        dd_mode=None,
        dd_strategy=None,
        **kwargs,
    ) -> IQMJob:
        """Submit one or more IQM circuits to the configured server."""
        if kwargs:
            unsupported = ", ".join(sorted(kwargs))
            raise ValueError(f"Unsupported keyword arguments: {unsupported}")

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

    # pylint: disable-next=arguments-differ
    def run(
        self,
        run_input: Union[QuantumCircuit, list[QuantumCircuit]],
        *args,
        calibration_set_id=None,
        **kwargs,
    ) -> Union[IQMJob, list[IQMJob]]:
        """Run IQM jobs using one resolved calibration set for both preparation and submission."""
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        resolved_calibration_set_id = self._resolve_calibration_set_id(calibration_set_id)
        run_input_compat = [
            self.apply_runtime_profile(program, calibration_set_id=resolved_calibration_set_id)
            for program in run_input
        ]
        run_input_compat = run_input_compat[0] if is_single_input else run_input_compat
        return self.submit(
            run_input_compat,
            *args,
            calibration_set_id=resolved_calibration_set_id,
            **kwargs,
        )

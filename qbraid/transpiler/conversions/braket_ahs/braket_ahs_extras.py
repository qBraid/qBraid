# Copyright 2025 qBraid
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
Module defining Amazon Braket AHS conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from braket.ahs import AnalogHamiltonianSimulation

from qbraid.transpiler.annotations import requires_extras

if TYPE_CHECKING:
    import bloqade.analog.builder.assign


@requires_extras("bloqade")
def bloqade_to_braket_ahs(
    program: bloqade.analog.builder.assign.BatchAssign,
) -> list[AnalogHamiltonianSimulation]:
    """Converts a Bloqade program batch to a list of Amazon Braket AHS.

    Args:
        program (BatchAssign): Bloqade program batch

    Returns:
        list[AnalogHamiltonianSimulation]: A list of Amazon Braket AHS programs
    """
    # pylint: disable=import-outside-toplevel
    from bloqade.analog.compiler.passes.hardware import (
        analyze_channels,
        assign_circuit,
        canonicalize_circuit,
        generate_ahs_code,
        generate_braket_ir,
        validate_waveforms,
    )

    braket_device_route = program.braket
    braket_hardware_routine = braket_device_route.aquila()

    circuit, params = braket_hardware_routine.circuit, braket_hardware_routine.params

    capabilities = braket_hardware_routine.backend.get_capabilities(use_experimental=False)

    task_specs = []

    for _, batch_params in enumerate(params.batch_assignments()):
        assignments = {**batch_params, **params.static_params}
        final_circuit, _ = assign_circuit(circuit, assignments)

        level_couplings = analyze_channels(final_circuit)
        final_circuit = canonicalize_circuit(final_circuit, level_couplings)

        validate_waveforms(level_couplings, final_circuit)
        ahs_components = generate_ahs_code(capabilities, level_couplings, final_circuit)

        task_ir = generate_braket_ir(ahs_components, 0)
        ahs_program = AnalogHamiltonianSimulation.from_ir(task_ir.program)

        task_specs.append(ahs_program)

    return task_specs

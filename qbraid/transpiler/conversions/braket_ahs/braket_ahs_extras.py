# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining Amazon Braket AHS conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from braket.ahs import AnalogHamiltonianSimulation

from qbraid.transpiler.annotations import requires_extras

if TYPE_CHECKING:
    import bloqade.builder.assign


@requires_extras("bloqade")
def bloqade_to_braket_ahs(
    program: bloqade.builder.assign.BatchAssign,
) -> list[AnalogHamiltonianSimulation]:
    """Converts a Bloqade program batch to a list of Amazon Braket AHS.

    Args:
        program (BatchAssign): Bloqade program batch

    Returns:
        list[AnalogHamiltonianSimulation]: A list of Amazon Braket AHS programs
    """
    # pylint: disable=import-outside-toplevel
    from bloqade.compiler.passes.hardware import (
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

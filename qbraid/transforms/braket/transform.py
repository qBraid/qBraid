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
Module for transforming Amazon Braket programs.

"""
from typing import TYPE_CHECKING, Union

from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.circuits import Circuit
from qbraid_core._import import LazyLoader

from qbraid.programs import NATIVE_REGISTRY, QPROGRAM_REGISTRY
from qbraid.programs.libs.braket import BraketCircuit
from qbraid.transforms.exceptions import DeviceProgramTypeMismatchError
from qbraid.transpiler import transpile

pytket_ionq = LazyLoader("pytket_ionq", globals(), "qbraid.transforms.pytket.ionq")

if TYPE_CHECKING:
    from qbraid.runtime.braket import BraketDevice


def transform(
    program: "Union[Circuit, AnalogHamiltonianSimulation]", device: "BraketDevice"
) -> "Union[Circuit, AnalogHamiltonianSimulation]":
    """Transpile a circuit for the device."""
    if device.profile is None:
        return program

    provider = (device.profile.get("provider") or "").upper()
    action_type = (device.profile.get("action_type") or "").upper()
    device_type: str = device.device_type.name

    if action_type == "OPENQASM":
        if not isinstance(program, Circuit):
            raise DeviceProgramTypeMismatchError(program, str(Circuit), action_type)

        if device_type == "SIMULATOR":
            qprogram = BraketCircuit(program)
            qprogram.remove_idle_qubits()
            program = qprogram.program

        elif provider == "IONQ":
            graph = device.scheme.conversion_graph
            if (
                graph is not None
                and graph.has_edge("pytket", "braket")
                and QPROGRAM_REGISTRY["pytket"] == NATIVE_REGISTRY["pytket"]
                and QPROGRAM_REGISTRY["braket"] == NATIVE_REGISTRY["braket"]
                and device._target_spec.alias == "braket"
            ):
                tk_circuit = transpile(program, "pytket", max_path_depth=1, conversion_graph=graph)
                tk_transformed = pytket_ionq.harmony_transform(tk_circuit)
                braket_transformed = transpile(
                    tk_transformed, "braket", max_path_depth=1, conversion_graph=graph
                )
                program = braket_transformed

    elif action_type == "AHS":
        if not isinstance(program, AnalogHamiltonianSimulation):
            raise DeviceProgramTypeMismatchError(
                program, str(AnalogHamiltonianSimulation), action_type
            )

        if device_type == "QPU":
            program = program.discretize(device._device)

    return program

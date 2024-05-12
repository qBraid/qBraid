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
Module for transforming Amazon Braket circuits.

"""
from typing import TYPE_CHECKING

from qbraid._import import LazyLoader
from qbraid.programs import NATIVE_REGISTRY, QPROGRAM_REGISTRY
from qbraid.programs.libs.braket import BraketCircuit
from qbraid.transpiler import transpile

pytket_ionq = LazyLoader("pytket_ionq", globals(), "qbraid.transforms.pytket.ionq")

if TYPE_CHECKING:
    import braket.circuits

    import qbraid.runtime.braket


def transform(
    circuit: "braket.circuits.Circuit", device: "qbraid.runtime.braket.BraketDevice"
) -> "braket.circuits.Circuit":
    """Transpile a circuit for the device."""
    if device.device_type.name == "SIMULATOR":
        program = BraketCircuit(circuit)
        program.remove_idle_qubits()
        return program.program

    if device.id == "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony":
        graph = device.scheme.conversion_graph
        if (
            graph is not None
            and graph.has_edge("pytket", "braket")
            and QPROGRAM_REGISTRY["pytket"] == NATIVE_REGISTRY["pytket"]
            and QPROGRAM_REGISTRY["braket"] == NATIVE_REGISTRY["braket"]
            and device._target_spec.alias == "braket"
        ):
            tk_circuit = transpile(circuit, "pytket", max_path_depth=1, conversion_graph=graph)
            tk_transformed = pytket_ionq.harmony_transform(tk_circuit)
            braket_transformed = transpile(
                tk_transformed, "braket", max_path_depth=1, conversion_graph=graph
            )
            return braket_transformed

    return circuit

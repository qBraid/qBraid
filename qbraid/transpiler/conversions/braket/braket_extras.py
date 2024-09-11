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
Module defining Amazon Braket conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

qiskit_braket_provider = LazyLoader("qiskit_braket_provider", globals(), "qiskit_braket_provider")
pytket_braket = LazyLoader("pytket_braket", globals(), "pytket.extensions.braket")

if TYPE_CHECKING:
    import braket.circuits
    import pytket.circuit
    import qiskit.circuit


@requires_extras("qiskit_braket_provider")
def braket_to_qiskit(circuit: braket.circuits.Circuit) -> qiskit.circuit.QuantumCircuit:
    """Return a Qiskit quantum circuit from a Braket quantum circuit.

    Args:
        circuit (Circuit): Braket quantum circuit

    Returns:
        QuantumCircuit: Qiskit quantum circuit
    """
    return qiskit_braket_provider.providers.adapter.to_qiskit(circuit)


@requires_extras("pytket.extensions.braket")
def braket_to_pytket(circuit: braket.circuits.Circuit) -> pytket.circuit.Circuit:
    """Returns a pytket circuit equivalent to the input Amazon Braket circuit.

    Args:
        circuit (braket.circuits.Circuit): Braket circuit to convert to a pytket circuit.

    Returns:
        pytket.circuit.Circuit: PyTKET circuit object equivalent to input Braket circuit.
    """
    return pytket_braket.braket_convert.braket_to_tk(circuit)

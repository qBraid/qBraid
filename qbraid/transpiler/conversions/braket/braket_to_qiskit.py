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
Module defining Qiskit to Amazon Braket conversion(s)

"""

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import requires_extras

if TYPE_CHECKING:
    import braket.circuits
    import qiskit.circuit


@requires_extras("qiskit_braket_provider")
def braket_to_qiskit(circuit: "braket.circuits.Circuit") -> "qiskit.circuit.QuantumCircuit":
    """Return a Qiskit quantum circuit from a Braket quantum circuit.

    Args:
        circuit (Circuit): Braket quantum circuit

    Returns:
        QuantumCircuit: Qiskit quantum circuit
    """
    # pylint: disable-next=import-outside-toplevel
    from qiskit_braket_provider.providers.adapter import to_qiskit  # type: ignore

    return to_qiskit(circuit)

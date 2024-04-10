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
def qiskit_to_braket(
    circuit: "qiskit.circuit.QuantumCircuit", **kwargs
) -> "braket.circuits.Circuit":
    """Return a Braket quantum circuit from a Qiskit quantum circuit.

    Args:
        circuit (QuantumCircuit): Qiskit quantum circuit
        basis_gates (Optional[Iterable[str]]): The gateset to transpile to.
            If `None`, the transpiler will use all gates defined in the Braket SDK.
            Default: `None`.
        verbatim (bool): Whether to translate the circuit without any modification, in other
            words without transpiling it. Default: False.

    Returns:
        Circuit: Braket circuit
    """
    # pylint: disable-next=import-outside-toplevel
    from qiskit_braket_provider.providers.adapter import to_braket  # type: ignore

    return to_braket(circuit, **kwargs)


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

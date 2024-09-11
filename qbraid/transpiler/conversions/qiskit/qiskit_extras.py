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
Module defining Qiskit conversion extras.

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

qiskit_braket_provider = LazyLoader("qiskit_braket_provider", globals(), "qiskit_braket_provider")
qiskit_qir = LazyLoader("qiskit_qir", globals(), "qiskit_qir")

if TYPE_CHECKING:
    import braket.circuits
    import pyqir
    import qiskit.circuit


@requires_extras("qiskit_braket_provider")
def qiskit_to_braket(circuit: qiskit.circuit.QuantumCircuit, **kwargs) -> braket.circuits.Circuit:
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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return qiskit_braket_provider.providers.adapter.to_braket(circuit, **kwargs)


@requires_extras("qiskit_qir")
def qiskit_to_pyqir(circuit: qiskit.circuit.QuantumCircuit) -> pyqir.Module:
    """Return a PyQIR module from a Qiskit quantum circuit.

    Args:
        circuit (QuantumCircuit): Qiskit quantum circuit

    Returns:
        Module: PyQIR module
    """
    # tuple of module and list of entry points
    module, _ = qiskit_qir.to_qir_module(circuit, record_output=False)
    return module

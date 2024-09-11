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
Module containing Cirq conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

stimcirq = LazyLoader("stimcirq", globals(), "stimcirq")
qbraid_qir = LazyLoader("qbraid_qir", globals(), "qbraid_qir")

if TYPE_CHECKING:
    import cirq
    import pyqir  # type: ignore
    import stim  # type: ignore


@requires_extras("stimcirq")
def cirq_to_stim(circuit: cirq.Circuit) -> stim.Circuit:
    """Returns an stim circuit equivalent to the input cirq circuit.

    Args:
        circuit (cirq.Circuit): cirq circuit to convert to stim circuit.

    Returns:
        stim.Circuit: stim circuit equivalent to input cirq circuit.
    """
    return stimcirq.cirq_circuit_to_stim_circuit(circuit)


@requires_extras("qbraid_qir")
def cirq_to_pyqir(circuit: cirq.Circuit) -> pyqir.Module:
    """Returns a PyQIR module equivalent to the input cirq circuit.

    Args:
        circuit (cirq.Circuit): cirq circuit to convert to PyQIR module.

    Returns:
        pyqir.Module: module equivalent to input cirq circuit.
    """
    return qbraid_qir.cirq.cirq_to_qir(circuit)

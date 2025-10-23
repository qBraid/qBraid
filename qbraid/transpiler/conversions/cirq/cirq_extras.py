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


@requires_extras("stim", "stimcirq")
def cirq_to_stim(circuit: cirq.Circuit) -> stim.Circuit:
    """Returns an stim circuit equivalent to the input cirq circuit.

    Args:
        circuit (cirq.Circuit): cirq circuit to convert to stim circuit.

    Returns:
        stim.Circuit: stim circuit equivalent to input cirq circuit.
    """
    return stimcirq.cirq_circuit_to_stim_circuit(circuit)


@requires_extras("stim", "stimcirq")
def stim_to_cirq(circuit: stim.Circuit) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input Stim circuit.

    Args:
        circuit (stim.Circuit): Stim circuit to convert to Cirq circuit.

    Returns:
        cirq.Circuit: Cirq circuit equivalent to input Stim circuit.
    """
    return stimcirq.stim_circuit_to_cirq_circuit(circuit)


@requires_extras("qbraid_qir")
def cirq_to_pyqir(circuit: cirq.Circuit) -> pyqir.Module:
    """Returns a PyQIR module equivalent to the input cirq circuit.

    Args:
        circuit (cirq.Circuit): cirq circuit to convert to PyQIR module.

    Returns:
        pyqir.Module: module equivalent to input cirq circuit.
    """
    return qbraid_qir.cirq.cirq_to_qir(circuit)

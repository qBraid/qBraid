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
Module containing PyTKET conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

pytket_braket = LazyLoader("pytket_braket", globals(), "pytket.extensions.braket")

if TYPE_CHECKING:
    import braket.circuits
    import pytket.circuit


@requires_extras("pytket.extensions.braket")
def pytket_to_braket(circuit: pytket.circuit.Circuit) -> braket.circuits.Circuit:
    """Returns an Amazon Braket circuit equivalent to the input pytket circuit.

    Args:
        circuit (pytket.circuit.Circuit): PyTKET circuit to convert to Braket circuit.

    Returns:
        braket.circuits.Circuit: Braket circuit equivalent to input pytket circuit.
    """
    braket_circuit, _, _ = pytket_braket.braket_convert.tk_to_braket(circuit)
    return braket_circuit

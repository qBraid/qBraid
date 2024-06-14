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
Unit tests for pytket circuit transformations.

"""
import braket.circuits
import pytest

from qbraid.programs.libs.pytket import IONQ_GATES, PytketCircuit
from qbraid.transpiler import transpile

from ..fixtures.braket.gates import get_braket_gates

braket_gates = get_braket_gates()


@pytest.mark.parametrize("gate_name", braket_gates)
def test_braket_ionq_transform(gate_name):
    """Test converting Amazon Braket circuit to use only IonQ supprted gates"""
    gate = braket_gates[gate_name]
    if gate.qubit_count == 1:
        source_circuit = braket.circuits.Circuit([braket.circuits.Instruction(gate, 0)])
    else:
        source_circuit = braket.circuits.Circuit(
            [braket.circuits.Instruction(gate, range(gate.qubit_count))]
        )

    pytket_source = transpile(source_circuit, "pytket")
    pytket_transformed = PytketCircuit.rebase(pytket_source, IONQ_GATES, 11)
    braket_transformed = transpile(pytket_transformed, "braket")
    assert isinstance(braket_transformed, braket.circuits.Circuit)

# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for Amazon Braket circuit compilation

"""
import braket
import pytest

from qbraid.compiler.braket import braket_ionq_compile

from .._data.braket.gates import get_braket_gates

braket_gates = get_braket_gates()


@pytest.mark.parametrize("gate_name", braket_gates)
def test_braket_ionq_compilation(gate_name):
    """Test converting Amazon Braket circuit to use only IonQ supprted gates"""
    gate = braket_gates[gate_name]
    if gate.qubit_count == 1:
        source_circuit = braket.circuits.Circuit([braket.circuits.Instruction(gate, 0)])
    else:
        source_circuit = braket.circuits.Circuit(
            [braket.circuits.Instruction(gate, range(gate.qubit_count))]
        )

        braket_circuit = braket_ionq_compile(source_circuit)
        assert isinstance(braket_circuit, braket.circuits.Circuit)

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
Unit tests for conversions between Qiskit circuits and Braket circuits
using OpenQASM 3.

"""

import numpy as np
from qiskit import QuantumCircuit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.qiskit_braket.conversions import qiskit_to_braket


def test_one_qubit_circuit_to_braket():
    """Test converting qiskit to braket for one qubit circuit."""
    qiskit_circuit = QuantumCircuit(1)
    qiskit_circuit.h(0)
    qiskit_circuit.ry(np.pi / 2, 0)
    braket_circuit = qiskit_to_braket(qiskit_circuit)
    circuits_allclose(qiskit_circuit, braket_circuit, strict_gphase=True)

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
import pytest

from qbraid.interface import circuits_allclose
from qbraid.interface.random_circuit import random_circuit
from qbraid.transpiler.qiskit_braket.conversions import qiskit_to_braket


@pytest.mark.skip("Feature stil in development")
@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5])
def test_random_circuit_to_braket(num_qubits):
    for _ in range(10):
        qiskit_circuit = random_circuit(
            "qiskit",
            num_qubits=num_qubits,
            depth=np.random.randint(5, 15),
        )
        braket_circuit = qiskit_to_braket(qiskit_circuit)
        assert circuits_allclose(braket_circuit, qiskit_circuit, strict_gphase=False)

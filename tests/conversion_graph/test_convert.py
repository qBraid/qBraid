# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
import logging

import cirq
import pytest

from qbraid.transpile import transpile

logging.basicConfig(level=logging.INFO)


@pytest.fixture
def cirq_circuit():
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.ops.H(q0), cirq.ops.CNOT(q0, q1))
    yield circuit


q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(cirq.ops.H(q0), cirq.ops.CNOT(q0, q1))

qasm_str = transpile(circuit, "qiskit")
print(qasm_str)

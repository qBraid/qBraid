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
Unit tests for the qbraid transpiler conversions module.

"""
from typing import Optional

import cirq
import numpy as np
import pytest

from qbraid.interface.circuit_equality import circuits_allclose
from qbraid.programs import NATIVE_REGISTRY, load_program
from qbraid.transpiler.conversions import conversion_functions
from qbraid.transpiler.conversions.cirq import cirq_to_qasm2
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.graph import ConversionGraph


def find_cirq_targets(skip: Optional[list[str]] = None):
    """Find all Cirq conversion targets."""
    skip = skip or []
    cirq_targets = []
    for function in conversion_functions:
        if function.startswith("cirq_to_"):
            _, target_library = function.split("_to_")
            if target_library not in skip and target_library in NATIVE_REGISTRY:
                cirq_targets.append(target_library)
    return cirq_targets


TARGETS = find_cirq_targets()


@pytest.mark.parametrize("frontend", TARGETS)
def test_convert_circuit_operation_from_cirq(frontend):
    """Test converting Cirq FrozenCircuit operation to OpenQASM"""
    q = cirq.NamedQubit("q")
    cirq_circuit = cirq.Circuit(
        cirq.Y(q), cirq.CircuitOperation(cirq.FrozenCircuit(cirq.X(q)), repetitions=5), cirq.Z(q)
    )

    graph = ConversionGraph()

    if not graph.has_path("cirq", frontend):
        pytest.skip(f"conversion from cirq to {frontend} not yet supported")

    test_circuit = transpile(cirq_circuit, frontend, conversion_graph=graph)

    cirq_unitary = load_program(cirq_circuit).unitary()

    try:
        test_unitary = load_program(test_circuit).unitary()
    except NotImplementedError:
        pytest.skip(f"Unitary calculation not implemented for {frontend}")

    assert np.allclose(cirq_unitary, test_unitary)


@pytest.mark.parametrize("frontend", TARGETS)
def test_convert_circuit_with_global_phase_from_cirq(frontend):
    """Test converting Cirq circuit with global phase to PyQuil"""
    q0, q1 = cirq.NamedQubit("q0"), cirq.NamedQubit("q1")
    cirq_circuit = cirq.Circuit(cirq.Y(q1).controlled_by(q0))

    graph = ConversionGraph()

    if not graph.has_path("cirq", frontend):
        pytest.skip(f"conversion from cirq to {frontend} not yet supported")

    test_circuit = transpile(cirq_circuit, frontend, conversion_graph=graph)

    try:
        load_program(test_circuit).unitary()
    except NotImplementedError:
        pytest.skip(f"Unitary calculation not implemented for {frontend}")

    assert circuits_allclose(cirq_circuit, test_circuit)


def test_cirq_to_qasm2_declares_cregs_in_key_order():
    """Classical registers follow the measurement keys, not the moments.

    Cirq schedules a measurement on an idle qubit into an earlier moment and declares its
    register first, so ``c_2`` preceded ``c_0``. Consumers that flatten the registers into
    one readout region do so in declaration order, which then permutes the bits relative
    to the keys.
    """
    q = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(
        cirq.ops.X(q[0]),
        cirq.ops.X(q[1]),  # q[2] is idle, so its measurement packs into moment 0
        [cirq.ops.measure(qb, key=f"c_{i}") for i, qb in enumerate(q)],
    )
    cregs = [line for line in cirq_to_qasm2(circuit).splitlines() if line.startswith("creg")]
    assert cregs == ["creg m_c_0[1];", "creg m_c_1[1];", "creg m_c_2[1];"]


def test_cirq_to_pyquil_via_qasm2_keeps_readout_bit_order():
    """The composed route lands qubit i in bit i, as the direct edge does.

    Regression test for the readout permutation: preparing the asymmetric pattern (1,1,0)
    read back as (0,1,1) through this route, because the flattened register followed
    declaration order and cirq had declared the registers out of key order.
    """
    pytest.importorskip("pyquil")  # capped below Python 3.13
    q = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(
        cirq.ops.X(q[0]),
        cirq.ops.X(q[1]),
        [cirq.ops.measure(qb, key=f"c_{i}") for i, qb in enumerate(q)],
    )
    from qbraid.transpiler.conversions.qasm2 import (  # pylint: disable=import-outside-toplevel
        qasm2_to_pyquil,
    )

    program = qasm2_to_pyquil(cirq_to_qasm2(circuit))
    # Statement order still follows the moments; what matters is which bit each qubit
    # lands in, so assert the mapping rather than the order the MEASUREs appear in.
    bit_to_qubit = {}
    for line in program.out().splitlines():
        if line.startswith("MEASURE"):
            _, qubit, register = line.split()
            bit_to_qubit[int(register.split("[")[1].rstrip("]"))] = int(qubit)
    assert bit_to_qubit == {0: 0, 1: 1, 2: 2}


def test_cirq_to_qasm2_leaves_unindexed_creg_names_in_place():
    """Keys without a trailing index keep their relative order and their own register.

    Reordering only makes sense for keys that name a bit position (``c_0``, ``c_1``).
    A key like ``alpha`` carries no index, so there is nothing to sort it by and the
    declaration it produced is left where cirq put it -- each qubit still measures into
    its own register, which is what the reorder must not disturb.
    """
    q = cirq.LineQubit.range(3)
    keys = ["alpha", "beta", "gamma"]
    circuit = cirq.Circuit(
        cirq.ops.X(q[0]),
        cirq.ops.X(q[1]),
        [cirq.ops.measure(qb, key=key) for qb, key in zip(q, keys)],
    )
    qasm = cirq_to_qasm2(circuit)
    cregs = [line for line in qasm.splitlines() if line.startswith("creg")]
    assert sorted(cregs) == sorted(f"creg m_{key}[1];" for key in keys)

    # every qubit still lands in its own register, one bit each
    measures = [line for line in qasm.splitlines() if line.startswith("measure")]
    assert len(measures) == len(keys)
    assert len({line.split("->")[1].strip() for line in measures}) == len(keys)

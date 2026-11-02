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
import sympy

from qbraid.interface.circuit_equality import circuits_allclose
from qbraid.programs import NATIVE_REGISTRY, load_program
from qbraid.transpiler.conversions import conversion_functions
from qbraid.transpiler.conversions.cirq import cirq_to_qasm2
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.exceptions import ProgramConversionError
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


@pytest.mark.parametrize("num_qubits", [3, 12])
@pytest.mark.parametrize("key_style", ["default", "invalid", "indexed", "mixed"])
def test_cirq_qasm2_readout_uses_original_keys(num_qubits, key_style):
    """Default and invalid keys must not rotate readout when moments differ (#1502)."""
    pytest.importorskip("pyquil")
    from qbraid.transpiler.conversions.cirq import (  # pylint: disable=import-outside-toplevel
        cirq_to_pyquil,
    )
    from qbraid.transpiler.conversions.qasm2 import (  # pylint: disable=import-outside-toplevel
        qasm2_to_pyquil,
    )

    qubits = cirq.LineQubit.range(num_qubits)
    if key_style == "default":
        measurements = cirq.measure_each(*qubits)
    else:
        if key_style == "invalid":
            # Include punctuation and already-valid names.
            keys = [f"a({i})" if i % 2 else f"a_{i}_" for i in range(num_qubits)]
        elif key_style == "indexed":
            keys = [f"c_{num_qubits - 1 - i}" for i in range(num_qubits)]
        else:
            # The first two keys collide if punctuation is replaced with underscores.
            keys = ["q(0)", "q_0_", "0", *[f"c_{i}" for i in range(3, num_qubits)]]
        measurements = [cirq.measure(q, key=k) for q, k in zip(qubits, keys)]
    circuit = cirq.Circuit(cirq.X(qubits[0]), measurements)
    original = circuit.copy()
    qasm = cirq_to_qasm2(circuit)
    expected = (
        {i: num_qubits - 1 - i for i in range(num_qubits)}
        if key_style == "indexed"
        else {i: i for i in range(num_qubits)}
    )
    for program in [cirq_to_pyquil(circuit), qasm2_to_pyquil(qasm)]:
        mapping = {}
        for line in program.out().splitlines():
            if line.startswith("MEASURE"):
                _, qubit, register = line.split()
                mapping[int(register.split("[")[1].rstrip("]"))] = int(qubit)
        assert mapping == expected
    assert circuit == original


@pytest.mark.parametrize("grouped", [False, True])
def test_cirq_qasm2_readout_preserves_values_and_invert_masks(grouped):
    """An asymmetric result survives anonymous keys, grouping and inverted readout."""
    pytest.importorskip("pyquil")
    from qbraid.transpiler.conversions.pyquil import (  # pylint: disable=import-outside-toplevel
        pyquil_to_cirq,
    )
    from qbraid.transpiler.conversions.qasm2 import (  # pylint: disable=import-outside-toplevel
        qasm2_to_pyquil,
    )

    q = cirq.LineQubit.range(4)
    if grouped:
        # Keep the order inside a multi-qubit measurement, even when reversed.
        measurements = [cirq.measure(q[1], q[0]), cirq.measure(q[3], q[2], invert_mask=(True,))]
        expected = [0, 1, 1, 0]
    else:
        measurements = [cirq.measure(qubit, invert_mask=(i == 2,)) for i, qubit in enumerate(q)]
        expected = [1, 0, 1, 0]
    circuit = cirq.Circuit(cirq.X(q[0]), measurements)
    converted = pyquil_to_cirq(qasm2_to_pyquil(cirq_to_qasm2(circuit)))
    result = cirq.Simulator().run(converted, repetitions=3).measurements
    actual = [int(result[f"ro[{i}]"][0][0]) for i in range(4)]
    assert actual == expected


def test_cirq_qasm2_repeated_key_keeps_both_measurements():
    """Repeated keys share one register without losing either measurement statement."""
    q = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.measure(q[0]), cirq.X(q[0]), cirq.measure(q[0]), cirq.measure(q[1]))
    qasm = cirq_to_qasm2(circuit)
    assert len([line for line in qasm.splitlines() if line.startswith("creg")]) == 2
    measures = [line for line in qasm.splitlines() if line.startswith("measure")]
    assert measures.count("measure q[0] -> m0[0];") == 2
    assert measures.count("measure q[1] -> m1[0];") == 1


def test_cirq_to_qasm2_orders_unindexed_keys_by_qubit():
    """Keys without a bit index follow qubit order, as in the direct Quil edge."""
    q = cirq.LineQubit.range(3)
    keys = ["alpha", "beta", "gamma"]
    circuit = cirq.Circuit(
        cirq.ops.X(q[0]),
        cirq.ops.X(q[1]),
        [cirq.ops.measure(qb, key=key) for qb, key in zip(q, keys)],
    )
    qasm = cirq_to_qasm2(circuit)
    cregs = [line for line in qasm.splitlines() if line.startswith("creg")]
    assert cregs == [f"creg m_{key}[1];" for key in keys]

    # every qubit still lands in its own register, one bit each
    measures = [line for line in qasm.splitlines() if line.startswith("measure")]
    assert len(measures) == len(keys)
    assert len({line.split("->")[1].strip() for line in measures}) == len(keys)


def test_cirq_to_qasm2_rejects_unresolved_parameters():
    """The direct QASM 2 edge reports every unresolved parameter by name."""
    alpha, theta = sympy.symbols("alpha theta")
    circuit = cirq.Circuit(
        cirq.rx(theta).on(cirq.LineQubit(0)), cirq.ry(alpha).on(cirq.LineQubit(1))
    )

    with pytest.raises(
        ProgramConversionError,
        match=(
            r"Cannot convert a Cirq circuit to OpenQASM 2 with unresolved parameters: "
            r"alpha, theta\. Resolve the parameters before conversion\."
        ),
    ):
        cirq_to_qasm2(circuit)


def test_cirq_to_qasm2_ignores_global_phase_parameters():
    """Parameters used only in a discarded global phase remain accepted."""
    theta = sympy.Symbol("theta")
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.H(qubit), cirq.global_phase_operation(sympy.exp(1j * theta)))

    qasm = cirq_to_qasm2(circuit)

    assert "h q[0];" in qasm


@pytest.mark.parametrize("target", ["braket", "qasm2", "qasm3"])
def test_transpile_parameterized_cirq_reports_unresolved_names(target):
    """Real conversion paths name symbolic inputs instead of leaking numeric errors."""
    theta = sympy.Symbol("theta")
    circuit = cirq.Circuit(cirq.rx(theta).on(cirq.LineQubit(0)))

    with pytest.raises(ProgramConversionError) as exc_info:
        transpile(circuit, target)

    message = str(exc_info.value)
    assert "unresolved parameters: theta" in message
    assert "TypeError:" not in message

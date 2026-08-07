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
Tests that conversions preserve which qubit's outcome lands in which readout bit.

The structural checks in ``test_measurement_coverage.py`` assert that a converted program
declares one readout register and measures every qubit into it exactly once. A converter
that permutes the readout satisfies all of that while returning the wrong answer, so these
tests execute the programs instead: each circuit prepares a deterministic, asymmetric
bit pattern, making any permutation of the readout observable in the result.

"""
import re

import cirq
import pytest
from cirq import ops as cirq_ops

# X on these qubits, so the expected readout is 1,1,0. Every rotation and the reversal of
# this pattern is distinct from it, so any permutation of the readout changes the result --
# a palindrome such as (1, 0, 1) would hide a reversed register. It also differs from the
# all-ones and all-zeros strings a broken converter tends to produce.
PATTERN = (1, 1, 0)
NUM_QUBITS = len(PATTERN)


def _cirq_prepared(qubits) -> cirq.Circuit:
    """Circuit preparing PATTERN on the given qubits, without measurement."""
    return cirq.Circuit(cirq_ops.X(qubits[i]) for i, bit in enumerate(PATTERN) if bit)


def _braket_counts(circuit) -> str:
    """Run a Braket circuit on the local simulator and return its single outcome."""
    from braket.devices import LocalSimulator  # pylint: disable=import-outside-toplevel

    counts = LocalSimulator("braket_sv").run(circuit, shots=10).result().measurement_counts
    assert len(counts) == 1, f"expected a deterministic outcome, got {dict(counts)}"
    return next(iter(counts))


def _measured_in_qubit_order(qubits, qubit_to_key: dict[int, int]) -> cirq.Circuit:
    """PATTERN, then one terminal measurement per qubit appended in qubit order.

    Appending in qubit order while the keys are permuted is what makes operation order and
    key order disagree -- the condition under which an op-order merge transposes the
    readout. Appending in key order instead makes the two coincide and hides the bug.
    """
    circuit = _cirq_prepared(qubits)
    for qubit_index in sorted(qubit_to_key):
        key = f"c_{qubit_to_key[qubit_index]}"
        circuit.append(cirq.Moment(cirq_ops.measure(qubits[qubit_index], key=key)))
    return circuit


@pytest.mark.parametrize(
    "qubit_to_key",
    [
        {0: 0, 1: 1, 2: 2},  # identity: op order and key order agree
        {0: 2, 1: 1, 2: 0},  # reversed
        {0: 1, 1: 2, 2: 0},  # rotated
        {0: 2, 1: 0, 2: 1},  # rotated the other way
    ],
)
def test_cirq_merge_preserves_per_key_values(qubit_to_key):
    """Merging terminal measurements must keep bit i holding what key ``c_i`` held.

    The merge collapses per-bit keys into one register, so it has to choose a bit order.
    Taking it from the order operations appear in transposes the readout whenever the keys
    are assigned in a different order than the measurements are applied.
    """
    from qbraid.transpiler.conversions.cirq.cirq_to_pyquil import (  # pylint: disable=import-outside-toplevel
        _merge_terminal_measurements,
    )

    qubits = cirq.LineQubit.range(NUM_QUBITS)
    circuit = _measured_in_qubit_order(qubits, qubit_to_key)
    key_to_qubit = {key: qubit for qubit, key in qubit_to_key.items()}

    merged = _merge_terminal_measurements(circuit)

    original_run = cirq.Simulator().run(circuit, repetitions=1).measurements
    merged_run = cirq.Simulator().run(merged, repetitions=1).measurements
    assert len(merged_run) == 1, f"expected one merged register, got {sorted(merged_run)}"

    merged_bits = list(next(iter(merged_run.values()))[0])
    expected = [int(original_run[f"c_{i}"][0][0]) for i in sorted(key_to_qubit)]
    assert merged_bits == expected

    # and the values are the ones the pattern implies, not merely self-consistent
    assert expected == [PATTERN[key_to_qubit[i]] for i in sorted(key_to_qubit)]


def test_cirq_to_pyquil_readout_index_follows_key():
    """The Quil readout bit for a qubit must be the index its measurement key names."""
    pytest.importorskip("pyquil", reason="pyquil not installed")
    from qbraid.transpiler.conversions.cirq import (  # pylint: disable=import-outside-toplevel
        cirq_to_pyquil,
    )

    qubits = cirq.LineQubit.range(NUM_QUBITS)
    # q0 -> c_1, q1 -> c_2, q2 -> c_0, measured in qubit order, so key order is q2, q0, q1
    qubit_to_key = {0: 1, 1: 2, 2: 0}
    circuit = _measured_in_qubit_order(qubits, qubit_to_key)
    key_to_qubit = {key: qubit for qubit, key in qubit_to_key.items()}

    program = cirq_to_pyquil(circuit)

    measured = {}
    for line in program.out().splitlines():
        match = re.fullmatch(r"MEASURE (\d+) \S+\[(\d+)\]", line)
        if match:
            measured[int(match.group(2))] = int(match.group(1))

    assert measured == key_to_qubit


def test_braket_to_cirq_preserves_readout_order():
    """Braket's keyless terminal measurements keep their order through the merge to one key."""
    pytest.importorskip("braket", reason="amazon-braket-sdk not installed")
    from braket.circuits import Circuit as BKCircuit  # pylint: disable=import-outside-toplevel

    from qbraid.transpiler.conversions.braket import (  # pylint: disable=import-outside-toplevel
        braket_to_cirq,
    )

    braket_circuit = BKCircuit()
    for index, bit in enumerate(PATTERN):
        if bit:
            braket_circuit.x(index)  # pylint: disable=no-member
    for index in range(NUM_QUBITS):
        braket_circuit.measure(index)

    converted = braket_to_cirq(braket_circuit)

    run = cirq.Simulator().run(converted, repetitions=1).measurements
    assert len(run) == 1, f"expected one merged register, got {sorted(run)}"
    assert list(next(iter(run.values()))[0]) == list(PATTERN)


def test_braket_to_cirq_orders_readout_by_classical_index():
    """Braket readout order is the Measure's classical bit index, not instruction order.

    ``Circuit.from_ir`` preserves permuted mappings such as ``b[2] = measure q[0]``, and
    Braket's own simulator honors them. The permutation is a rotation, not a reversal, so
    an endianness flip cannot masquerade as the correct answer.
    """
    pytest.importorskip("braket", reason="amazon-braket-sdk not installed")
    # pylint: disable-next=import-outside-toplevel
    from braket.circuits import Circuit as BKCircuit
    from braket.circuits import Instruction, Measure  # pylint: disable=import-outside-toplevel

    from qbraid.transpiler.conversions.braket import (  # pylint: disable=import-outside-toplevel
        braket_to_cirq,
    )

    braket_circuit = BKCircuit()
    for index, bit in enumerate(PATTERN):
        if bit:
            braket_circuit.x(index)  # pylint: disable=no-member
    qubit_to_bit = {0: 1, 1: 2, 2: 0}
    for qubit, classical_bit in qubit_to_bit.items():
        braket_circuit.add_instruction(Instruction(Measure(index=classical_bit), qubit))

    converted = braket_to_cirq(braket_circuit)

    run = cirq.Simulator().run(converted, repetitions=1).measurements
    assert len(run) == 1, f"expected one merged register, got {sorted(run)}"
    bit_to_qubit = {bit: qubit for qubit, bit in qubit_to_bit.items()}
    expected = [PATTERN[bit_to_qubit[i]] for i in range(NUM_QUBITS)]
    assert list(next(iter(run.values()))[0]) == expected


def test_cirq_to_braket_preserves_readout_order():
    """Each Cirq measurement must land on its own Braket classical bit, in qubit order.

    Braket's ``Measure`` defaults its index to 0, so building the instructions directly
    (rather than via ``Circuit.measure()``) collapses every readout onto ``b[0]`` unless
    the index is supplied.
    """
    pytest.importorskip("braket", reason="amazon-braket-sdk not installed")
    from qbraid.transpiler.conversions.cirq import (  # pylint: disable=import-outside-toplevel
        cirq_to_braket,
    )

    qubits = cirq.LineQubit.range(NUM_QUBITS)
    circuit = _cirq_prepared(qubits)
    circuit.append(cirq_ops.measure(*qubits, key="m"))

    converted = cirq_to_braket(circuit)

    assert _braket_counts(converted) == "".join(str(bit) for bit in PATTERN)


def test_cirq_to_braket_invert_mask_lands_on_distinct_bits():
    """An inverted measurement flips its own bit and no other."""
    pytest.importorskip("braket", reason="amazon-braket-sdk not installed")
    from qbraid.transpiler.conversions.cirq import (  # pylint: disable=import-outside-toplevel
        cirq_to_braket,
    )

    qubits = cirq.LineQubit.range(NUM_QUBITS)
    invert_mask = (True, False, True)
    circuit = cirq.Circuit(cirq_ops.measure(*qubits, key="m", invert_mask=invert_mask))

    converted = cirq_to_braket(circuit)

    expected = "".join(str(int(flipped)) for flipped in invert_mask)
    assert _braket_counts(converted) == expected


def test_pytket_to_braket_preserves_classical_bit_order():
    """A pytket measurement into bit ``i`` must land in Braket's bit ``i``.

    ``tk_to_braket`` drops measurements, so the converter re-adds them from the source's
    qubit-to-bit map. That map is what decides readout order, and a pytket circuit is free
    to measure qubit 0 into a bit other than 0.
    """
    pytest.importorskip("pytket", reason="pytket not installed")
    pytest.importorskip("braket", reason="amazon-braket-sdk not installed")
    from pytket.circuit import Circuit as TKCircuit  # pylint: disable=import-outside-toplevel

    from qbraid.transpiler.conversions.pytket import (  # pylint: disable=import-outside-toplevel
        pytket_to_braket,
    )

    tk_circuit = TKCircuit(NUM_QUBITS, NUM_QUBITS)
    for index, bit in enumerate(PATTERN):
        if bit:
            tk_circuit.X(index)
    qubit_to_bit = {0: 2, 1: 0, 2: 1}
    for qubit, classical_bit in qubit_to_bit.items():
        tk_circuit.Measure(qubit, classical_bit)

    converted = pytket_to_braket(tk_circuit)

    bit_to_qubit = {bit: qubit for qubit, bit in qubit_to_bit.items()}
    expected = "".join(str(PATTERN[bit_to_qubit[i]]) for i in range(NUM_QUBITS))
    assert _braket_counts(converted) == expected


def test_pytket_to_braket_remeasured_qubit_raises():
    """Measuring a qubit into a second classical bit is rejected, not silently dropped.

    Braket cannot represent it (measurement ends a qubit's life), and because the
    re-added measures are keyed by qubit, converting silently would emit one measure
    where the source declared two classical bits.
    """
    pytest.importorskip("pytket", reason="pytket not installed")
    pytest.importorskip("braket", reason="amazon-braket-sdk not installed")
    from pytket.circuit import Circuit as TKCircuit  # pylint: disable=import-outside-toplevel

    from qbraid.transpiler.conversions.pytket import (  # pylint: disable=import-outside-toplevel
        pytket_to_braket,
    )
    from qbraid.transpiler.exceptions import (  # pylint: disable=import-outside-toplevel
        ProgramConversionError,
    )

    tk_circuit = TKCircuit(1, 2)
    tk_circuit.X(0)
    tk_circuit.Measure(0, 0)
    tk_circuit.Measure(0, 1)

    with pytest.raises(ProgramConversionError, match="mid-circuit measurement"):
        pytket_to_braket(tk_circuit)

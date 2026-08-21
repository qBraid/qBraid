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
Unt tests for conversions to/from pyQuil circuits.

"""
import re

import numpy as np
import pytest
from cirq import Circuit, LineQubit, Moment, Simulator
from cirq import ops as cirq_ops

try:
    from pyquil import Program
    from pyquil.gates import CNOT, CZ, RESET, RX, RZ, RZZ, H, I, X, Y, Z
    from pyquil.noise import _decoherence_noise_model, _get_program_gates, apply_noise_model

    from qbraid.interface import circuits_allclose
    from qbraid.transpiler.conversions.cirq import cirq_to_pyquil, cirq_to_qasm2
    from qbraid.transpiler.conversions.cirq.cirq_to_pyquil import _merge_terminal_measurements
    from qbraid.transpiler.conversions.pyquil import pyquil_to_cirq
    from qbraid.transpiler.conversions.qasm2 import qasm2_to_cirq, qasm2_to_pyquil
    from qbraid.transpiler.converter import transpile
    from qbraid.transpiler.exceptions import ProgramConversionError

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def test_to_from_pyquil():
    """Test round trip pyQuil-Cirq conversions."""
    p = Program()
    p += X(0)
    p += Y(1)
    p += Z(2)
    p += CNOT(0, 1)
    p += CZ(1, 2)
    p_cirq = pyquil_to_cirq(p)
    p_test = cirq_to_pyquil(p_cirq)
    assert p.out() == p_test.out()


def test_to_from_pyquil_parameterized():
    """Test round trip pyQuil-Cirq conversions with parameterized gates."""
    q0, q1 = (0, 1)
    p = Program()
    p += H(q0)
    p += H(q1)
    p += CNOT(q0, q1)
    p += RZ(2 * np.pi, q1)
    p += CNOT(q0, q1)
    p += H(q0)
    p += H(q1)
    p += RZ(np.pi / 4, q0)
    p += RZ(np.pi / 4, q1)
    p += H(q0)
    p += H(q1)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert p.out() == p_test.out()


QUIL_STRING = """
I 0
I 1
I 2
X 0
Y 1
Z 2
RX(pi/2) 0
RY(pi/2) 1
RZ(pi/2) 2
H 0
CZ 0 1
CNOT 1 2
CPHASE(pi/2) 0 1
CPHASE00(pi/2) 1 2
CPHASE01(pi/2) 0 1
CPHASE10(pi/2) 1 2
ISWAP 0 1
SWAP 1 2
XY(pi/2) 0 1
CCNOT 0 1 2
CSWAP 0 1 2
"""


def test_to_from_pyquil_quil_string():
    """PHASE, PSWAP, S, T, declaration, and measurement don't convert back
    and forth perfectly (in terms of labels -- the program unitaries and
    number of measurements are equivalent)."""
    p = Program(QUIL_STRING)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert circuits_allclose(p, p_test)


def test_from_pyquil_no_zero_qubit():
    """Test converting a pyQuil program with a non-zero qubit index to Cirq."""
    p = Program()
    p += X(10)
    p += Y(11)
    p += Z(12)
    p += CNOT(10, 11)
    p += CZ(11, 12)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert p.out() == p_test.out()


def test_raise_error_to_pyquil_bit_flip():
    """Test raising an error when converting a Cirq circuit with a bit flip to pyQuil."""

    with pytest.raises(ProgramConversionError):
        q0 = LineQubit(0)
        circuit = Circuit(cirq_ops.bit_flip(p=0.2).on(q0), cirq_ops.measure(q0, key="result"))
        cirq_to_pyquil(circuit)


def test_raise_error_from_pyquil_noisey():
    """Test raising an error when converting a noisey pyQuil program to Cirq."""

    with pytest.raises(ProgramConversionError):
        p = Program()
        p += RX(-np.pi / 2, 0)
        noise_model = _decoherence_noise_model(_get_program_gates(p))
        p = apply_noise_model(p, noise_model)
        pyquil_to_cirq(p)


def test_cirq_to_quil_output_rzz():
    """Test that a RZZ gate is correctly converted to Quil."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    rzz(pi) q[0], q[1];
    rzz(0) q[0], q[1];
    rzz(pi/2) q[0], q[1];
    """

    p = Program()
    p += CZ(0, 1)
    p += I(0)
    p += I(1)
    p += RZZ(np.pi / 2, 0, 1)
    cirq_circuit = qasm2_to_cirq(qasm)
    p_test: Program = cirq_to_pyquil(cirq_circuit)
    assert p_test.out().replace("pi/2", f"{np.pi/2}") == p.out()


@pytest.mark.parametrize(
    "gate",
    [cirq_ops.XXPowGate, cirq_ops.YYPowGate, cirq_ops.ZZPowGate],
)
@pytest.mark.parametrize("exponent", [0.5, 1.0, 0.75, -0.8, 2.0, 0.0])
def test_cirq_to_pyquil_ising_gate_roundtrip(gate, exponent):
    """Cirq XX/YY/ZZ interaction gates round-trip through pyQuil exactly.

    Regression test for https://github.com/qBraid/qBraid/issues/386, where the
    non-integer-exponent cases were decomposed into single-qubit rotations that
    did not preserve the two-qubit unitary.
    """
    q0, q1 = LineQubit.range(2)
    cirq_in = Circuit(gate(exponent=exponent).on(q0, q1))
    cirq_out = pyquil_to_cirq(cirq_to_pyquil(cirq_in))
    assert circuits_allclose(cirq_in, cirq_out, strict_gphase=True)


@pytest.mark.parametrize("exponent", [0.5, 1.0, 0.75, -0.8, 2.0, 0.0])
def test_cirq_to_pyquil_swappow_roundtrip(exponent):
    """Cirq SwapPowGate round-trips through pyQuil exactly.

    Non-integer powers were previously emitted as ``PSWAP(pi*t)``, a parametric
    swap-with-phase whose unitary differs from a fractional ``SWAP**t``. They now
    fall back to cirq's CNOT / RY / CPHASE decomposition.
    """
    q0, q1 = LineQubit.range(2)
    cirq_in = Circuit(cirq_ops.SwapPowGate(exponent=exponent).on(q0, q1))
    cirq_out = pyquil_to_cirq(cirq_to_pyquil(cirq_in))
    assert circuits_allclose(cirq_in, cirq_out, strict_gphase=True)


@pytest.mark.parametrize(
    "instr", ["CPHASE00(pi/2) 0 1", "CPHASE01(pi/2) 0 1", "CPHASE10(pi/2) 0 1"]
)
def test_cirq_to_pyquil_two_qubit_diagonal_roundtrip(instr):
    """pyQuil CPHASExx gates round-trip through cirq.

    ``pyquil_to_cirq`` represents these as a ``TwoQubitDiagonalGate`` whose
    diagonal angles are stored as a complex array; ``cirq_to_pyquil`` previously
    raised ``TypeError`` formatting them (``Fraction`` of a complex value).
    """
    p = Program(instr)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert circuits_allclose(p, p_test)


def test_multi_key_terminal_measurements_merge_to_single_register():
    """Per-bit measurement keys (as produced by QASM import) coalesce into one
    readout register instead of one BIT[1] register per key."""
    qubits = LineQubit.range(3)
    circuit = Circuit(
        cirq_ops.H(qubits[0]),
        cirq_ops.CNOT(qubits[0], qubits[1]),
        cirq_ops.CNOT(qubits[1], qubits[2]),
        [cirq_ops.measure(qb, key=f"c_{i}") for i, qb in enumerate(qubits)],
    )
    program = cirq_to_pyquil(circuit)
    lines = program.out().splitlines()
    assert [line for line in lines if line.startswith("DECLARE")] == ["DECLARE ro BIT[3]"]
    assert [line for line in lines if line.startswith("MEASURE")] == [
        f"MEASURE {i} ro[{i}]" for i in range(3)
    ]


def test_merged_readout_order_follows_keys_not_moments():
    """Bit position comes from the measurement key, not the moment the measure sits in.

    Merging into one register has to choose a bit order; taking it from operation order
    silently transposes the readout whenever a later-indexed qubit is measured first.
    """
    qubits = LineQubit.range(3)
    circuit = Circuit(
        [cirq_ops.H(qubits[0]), cirq_ops.X(qubits[1]), cirq_ops.Y(qubits[2])],
        Moment(cirq_ops.measure(qubits[2], key="c_2")),
        Moment(cirq_ops.measure(qubits[0], key="c_0")),
        Moment(cirq_ops.measure(qubits[1], key="c_1")),
    )
    measures = [
        line for line in cirq_to_pyquil(circuit).out().splitlines() if line.startswith("MEASURE")
    ]
    assert measures == ["MEASURE 0 ro[0]", "MEASURE 1 ro[1]", "MEASURE 2 ro[2]"]


def test_merged_readout_order_honors_permuted_qasm_registers():
    """``measure q[2] -> c[0]`` must land q_2 in bit 0, whatever order the ops appear in."""
    qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c[3];
h q[0];
cx q[0],q[1];
measure q[2] -> c[0];
measure q[0] -> c[2];
measure q[1] -> c[1];
"""
    measures = [
        line
        for line in cirq_to_pyquil(qasm2_to_cirq(qasm)).out().splitlines()
        if line.startswith("MEASURE")
    ]
    assert measures == ["MEASURE 2 ro[0]", "MEASURE 1 ro[1]", "MEASURE 0 ro[2]"]


def test_merged_measurement_key_avoids_collision():
    """A mid-circuit measurement already keyed 'm' must not be duplicated by the merge."""
    qubits = LineQubit.range(2)
    circuit = Circuit(
        cirq_ops.H(qubits[0]),
        cirq_ops.measure(qubits[0], key="m"),
        cirq_ops.X(qubits[0]),
        cirq_ops.measure(qubits[0], key="c_0"),
        cirq_ops.measure(qubits[1], key="c_1"),
    )
    merged = _merge_terminal_measurements(circuit)

    keys = [
        op.gate.key
        for op in merged.all_operations()
        if isinstance(op.gate, cirq_ops.MeasurementGate)
    ]
    assert len(keys) == len(set(keys))
    Simulator().run(merged, repetitions=1)


def test_confusion_map_raises_rather_than_being_dropped():
    """A readout error matrix has no Quil equivalent, so merging it away would be silent."""
    qubits = LineQubit.range(2)
    circuit = Circuit(
        [cirq_ops.H(qubits[0]), cirq_ops.X(qubits[1])],
        cirq_ops.measure(
            qubits[0], key="c_0", confusion_map={(0,): np.array([[0.9, 0.1], [0.1, 0.9]])}
        ),
        cirq_ops.measure(qubits[1], key="c_1"),
    )
    with pytest.raises(ProgramConversionError, match="confusion map"):
        cirq_to_pyquil(circuit)


def test_single_terminal_measurement_is_left_alone():
    """Nothing to merge means the circuit is returned untouched, key included."""
    qubits = LineQubit.range(2)
    circuit = Circuit(
        cirq_ops.H(qubits[0]),
        cirq_ops.CNOT(qubits[0], qubits[1]),
        cirq_ops.measure(*qubits, key="result"),
    )
    assert _merge_terminal_measurements(circuit) is circuit


def test_cirq_reset_to_pyquil():
    """A Cirq circuit containing ``cirq.reset`` converts directly to a pyQuil
    program with a RESET on the same qubit, preserving operation order.

    Regression test: ``cirq_to_pyquil`` previously raised
    ``ProgramConversionError`` on any circuit containing ``cirq.ResetChannel``.
    """
    q0, q1 = LineQubit.range(2)
    circuit = Circuit(cirq_ops.X(q0), cirq_ops.reset(q0), cirq_ops.CNOT(q0, q1))
    p = Program()
    p += X(0)
    p += RESET(0)
    p += CNOT(0, 1)
    p_test = cirq_to_pyquil(circuit)
    assert p_test.out() == p.out()


def test_transpile_cirq_reset_to_pyquil_direct_path():
    """``transpile`` converts a circuit containing a reset over the direct
    ``cirq -> pyquil`` edge.

    Regression test: with ``max_path_depth=1`` this previously raised
    ``ProgramConversionError``, and the default search only succeeded by
    silently falling back to the ``cirq -> qasm2 -> pyquil`` path.
    """
    q0, q1 = LineQubit.range(2)
    circuit = Circuit(cirq_ops.X(q0), cirq_ops.reset(q0), cirq_ops.CNOT(q0, q1))
    program = transpile(circuit, "pyquil", max_path_depth=1)
    assert isinstance(program, Program)
    assert program.out() == "X 0\nRESET 0\nCNOT 0 1\n"


def test_single_measurement_key_declares_ro():
    """A lone measurement key becomes ``ro``, Quil's conventional readout register.

    Rigetti result parsers key on that name -- ``AzureResultBuilder`` looked up ``ro``
    outright -- so a program declaring ``m0`` submitted and ran but failed at result time.
    """
    qubits = LineQubit.range(2)
    circuit = Circuit(cirq_ops.H(qubits[0]), cirq_ops.measure(*qubits, key="result"))
    assert "DECLARE ro BIT[2]" in cirq_to_pyquil(circuit).out()


def test_multiple_measurement_keys_keep_positional_names():
    """Mid-circuit measurements leave several keys, none of which is unambiguously readout."""
    q0, q1 = LineQubit.range(2)
    circuit = Circuit(
        cirq_ops.measure(q0, key="mid"),
        cirq_ops.CNOT(q0, q1),
        cirq_ops.measure(q1, key="final"),
    )
    declares = [line for line in cirq_to_pyquil(circuit).out().splitlines() if "DECLARE" in line]
    assert declares == ["DECLARE m0 BIT[1]", "DECLARE m1 BIT[1]"]


@pytest.mark.parametrize(
    "body",
    [
        "qreg q[3]; creg c[3]; h q[0]; cx q[0],q[1]; x q[2]; "
        "measure q[0]->c[0]; measure q[1]->c[1]; measure q[2]->c[2];",
        "qreg q[2]; creg z[1]; creg a[1]; x q[0]; measure q[0]->z[0]; measure q[1]->a[0];",
        "qreg q[4]; creg z[2]; creg a[2]; x q[0]; x q[3]; measure q[0]->z[0]; "
        "measure q[1]->z[1]; measure q[2]->a[0]; measure q[3]->a[1];",
        "qreg q[3]; creg c[3]; x q[0]; measure q[2]->c[0]; measure q[1]->c[1]; "
        "measure q[0]->c[2];",
    ],
)
def test_direct_and_qasm2_routes_agree_on_readout(body):
    """Both routes from cirq to pyquil map each qubit to the same readout bit.

    The direct edge orders merged bits by measurement key and ``cirq -> qasm2`` sorts cregs
    by the same key (#1345), so the routes agree. MEASURE lines may still be emitted in a
    different order -- measurements on disjoint qubits commute -- so compare the mapping.
    """

    def readout_map(program):
        return dict(re.findall(r"MEASURE (\d+) (\w+\[\d+\])", program.out()))

    circuit = qasm2_to_cirq('OPENQASM 2.0;\ninclude "qelib1.inc";\n' + body)
    assert readout_map(cirq_to_pyquil(circuit)) == readout_map(
        qasm2_to_pyquil(cirq_to_qasm2(circuit))
    )

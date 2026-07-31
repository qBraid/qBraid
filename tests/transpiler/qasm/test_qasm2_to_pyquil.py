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
Unit tests for OpenQASM 2 to pyQuil conversion.

"""

import re

import pytest

try:
    # imported for the availability check as much as for use: the conversion module
    # itself imports pyQuil lazily, so it stays importable without pyQuil installed
    # and cannot stand in for the dependency here.
    from pyquil import Program

    from qbraid.transpiler import transpile
    from qbraid.transpiler.conversions.qasm2 import qasm2_to_pyquil

    pyquil_not_installed = False
except ImportError:  # pragma: no cover
    pyquil_not_installed = True

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


# Verbatim source of production job 6a6a76d629289824865a0b34
# (rigetti:rigetti:qpu:cepheus-1-108q), one of 26 jobs that failed at submit with
# 'Misplaced or illegal instruction in ProtoQuil program: MEASURE 3 m1[0] >>>H 1'.
# Every one of those 26 declares exactly one qreg and one creg with all measurements
# last, so the reordering quilc rejected was introduced by the conversion, not the user.
PROD_JOB_6A6A76D6 = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
creg c[4];
h q[0];
h q[1];
h q[1];
cx q[0], q[1];
h q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];
"""


def _expected_measure_map(qasm: str) -> dict[int, int]:
    """Derive the qubit -> flat classical bit map straight from the QASM source text.

    Deliberately independent of the converter: it re-reads the source with regexes and
    applies the OpenQASM rule that classical registers are laid out end to end in
    declaration order. A test that instead restated the converter's own output would
    pass just as happily if the converter assigned the wrong bit.

    Returns:
        dict[int, int]: qubit index -> flat ``ro`` bit index.
    """
    offsets: dict[str, int] = {}
    total = 0
    for name, size in re.findall(r"creg\s+(\w+)\[(\d+)\]\s*;", qasm):
        offsets[name] = total
        total += int(size)

    mapping: dict[int, int] = {}
    for qubit, reg, bit in re.findall(r"measure\s+\w+\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]\s*;", qasm):
        mapping[int(qubit)] = offsets[reg] + int(bit)
    return mapping


def _measure_map(program) -> dict[int, int]:
    """Read back the qubit -> ``ro`` bit map from the converted Quil MEASURE lines."""
    return {
        int(qubit): int(bit)
        for qubit, bit in re.findall(r"^MEASURE (\d+) ro\[(\d+)\]$", program.out(), re.MULTILINE)
    }


def test_production_job_converts_without_misplaced_instructions():
    """Regression test for the 26 Rigetti jobs quilc rejected as misplaced instructions.

    This is the test that would have caught the bug. Routing this program through Cirq
    (the fewest-hops path before this change) emitted four single-bit registers
    ``m0..m3`` and scheduled MEASUREs as early as each qubit was free, leaving gates
    after the first MEASURE. ProtoQuil forbids both.
    """
    lines = [line for line in qasm2_to_pyquil(PROD_JOB_6A6A76D6).out().splitlines() if line.strip()]

    assert [line for line in lines if line.startswith("DECLARE")] == ["DECLARE ro BIT[4]"]

    measures = [line for line in lines if line.startswith("MEASURE")]
    assert len(measures) == 4
    # the property ProtoQuil actually enforces: nothing follows the first MEASURE
    first_measure = next(i for i, line in enumerate(lines) if line.startswith("MEASURE"))
    assert lines[first_measure:] == measures


def test_production_job_measures_each_qubit_into_the_bit_the_source_names():
    """Every qubit lands in the classical bit the source's creg names."""
    program = qasm2_to_pyquil(PROD_JOB_6A6A76D6)
    assert isinstance(program, Program)
    assert _measure_map(program) == _expected_measure_map(PROD_JOB_6A6A76D6)


def test_whole_register_measure_form():
    """``measure q -> c;`` (production job 6a6618e30936bd6f4cecd3bd) maps bit for bit.

    This form is a single QASM statement, so it cannot have been written in a bad order;
    it still came back from the Cirq route reordered, which is what ruled out user input
    as the cause. pyqasm expands it to one measurement per qubit.
    """
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    creg c[3];
    h q[0];
    cx q[0], q[1];
    measure q -> c;
    """
    assert _measure_map(qasm2_to_pyquil(qasm)) == {0: 0, 1: 1, 2: 2}


def test_multiple_classical_registers_out_of_order():
    """Interleaved, out-of-order measurements across two cregs keep their bit indices.

    Constructed rather than copied from production: all 26 failing jobs declare a single
    creg, so no real program exercises multi-creg layout. It guards the highest-cost
    failure mode of this conversion, where a wrong qubit-to-bit map returns confidently
    wrong counts instead of raising.
    """
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[5];
    creg a[2];
    creg b[3];
    h q[0];
    measure q[2] -> b[0];
    x q[1];
    measure q[0] -> a[1];
    measure q[4] -> b[2];
    measure q[1] -> a[0];
    measure q[3] -> b[1];
    """
    program = qasm2_to_pyquil(qasm)

    # a[0:2] occupies ro[0:2], b[0:3] occupies ro[2:5]
    expected = {2: 2, 0: 1, 4: 4, 1: 0, 3: 3}
    assert _expected_measure_map(qasm) == expected, "source-derived layout"
    assert _measure_map(program) == expected
    assert "DECLARE ro BIT[5]" in program.out()


def test_transpile_qasm2_to_pyquil_keeps_measurements_last():
    """``transpile`` routes qasm2 -> pyquil without reordering measurements.

    Guards route selection as much as the conversion itself: ``transpile`` picks the
    fewest-hops path, so an edge added elsewhere in the graph could silently put this
    conversion back through Cirq.
    """
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[4];
    creg c[4];
    h q[0];
    cx q[0], q[1];
    h q[2];
    cx q[2], q[3];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    measure q[2] -> c[2];
    measure q[3] -> c[3];
    """
    instructions = [line for line in transpile(qasm, "pyquil").out().splitlines() if line.strip()]
    assert instructions.count("DECLARE ro BIT[4]") == 1
    measured = [line for line in instructions if line.startswith("MEASURE")]
    assert len(measured) == 4
    assert instructions[-4:] == measured


def test_creg_narrower_than_qreg():
    """A creg narrower than the qreg declares only the bits it has.

    Production jobs 6a5bede5d17a5abc1d707e18 and 6a5bede7d17a5abc1d707e1b declare
    ``qreg q[24]; creg c[9];``.
    """
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[4];
    creg c[2];
    h q[0];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    """
    program = qasm2_to_pyquil(qasm)
    assert "DECLARE ro BIT[2]" in program.out()
    assert _measure_map(program) == {0: 0, 1: 1}


def test_no_classical_register_declares_nothing():
    """A program with no creg converts and declares no readout register."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    h q[0];
    cx q[0], q[1];
    """
    out = qasm2_to_pyquil(qasm).out()
    assert "DECLARE" not in out
    assert "MEASURE" not in out


def test_same_qubit_measured_into_two_bits():
    """Measuring one qubit twice writes both classical bits it names."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[3];
    h q[0];
    measure q[0] -> c[0];
    measure q[0] -> c[1];
    measure q[1] -> c[2];
    """
    out = qasm2_to_pyquil(qasm).out()
    assert "DECLARE ro BIT[3]" in out
    assert re.findall(r"^MEASURE .*$", out, re.MULTILINE) == [
        "MEASURE 0 ro[0]",
        "MEASURE 0 ro[1]",
        "MEASURE 1 ro[2]",
    ]

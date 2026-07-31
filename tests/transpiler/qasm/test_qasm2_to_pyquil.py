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


def test_qasm2_to_pyquil_single_readout_register():
    """Every measurement lands in one ``ro`` register, at the source's creg index."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    creg c[3];
    h q[0];
    cx q[0], q[1];
    cx q[1], q[2];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    measure q[2] -> c[2];
    """
    program = qasm2_to_pyquil(qasm)
    assert isinstance(program, Program)
    assert program.out().splitlines() == [
        "DECLARE ro BIT[3]",
        "H 0",
        "CNOT 0 1",
        "CNOT 1 2",
        "MEASURE 0 ro[0]",
        "MEASURE 1 ro[1]",
        "MEASURE 2 ro[2]",
    ]


def test_qasm2_to_pyquil_multiple_classical_registers():
    """Several cregs are laid out end to end in ``ro``, in declaration order.

    The bit a qubit is measured into is the one the source names, not the order
    the measurements appear in, so ``q[0] -> a[1]`` really does land in ``ro[1]``.
    """
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    creg a[2];
    creg b[1];
    h q[0];
    cx q[0], q[1];
    measure q[0] -> a[1];
    measure q[1] -> a[0];
    measure q[2] -> b[0];
    """
    out = qasm2_to_pyquil(qasm).out().splitlines()
    assert out[0] == "DECLARE ro BIT[3]"
    assert out[-3:] == ["MEASURE 0 ro[1]", "MEASURE 1 ro[0]", "MEASURE 2 ro[2]"]


def test_transpile_qasm2_to_pyquil_keeps_measurements_last():
    """``transpile`` routes qasm2 -> pyquil without reordering measurements.

    Guards route selection as much as the conversion itself. The ``qasm2 -> cirq
    -> pyquil`` route rebuilds the program from Cirq moments, which schedules each
    measurement as early as it can and so emits gates on other qubits *after* a
    MEASURE. Rigetti's quilc rejects that as "Misplaced or illegal instruction in
    ProtoQuil program", so a program whose measurements all sit at the end of the
    source must still have them all at the end after conversion.
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

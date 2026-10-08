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
Unit tests for the OpenQASM 3 to OpenQASM 2 conversion.

"""
import pytest

from qbraid.transpiler import ConversionGraph, transpile
from qbraid.transpiler.conversions.qasm3 import qasm3_to_qasm2

HEADER = 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'


def test_partly_measured_register_keeps_its_name_and_width():
    """Unmeasured bits stay in place, so ``c[2]`` is still bit 2 of ``c``."""
    qasm2 = qasm3_to_qasm2(
        HEADER + "qubit[3] q;\nbit[3] c;\nx q[2];\nc[2] = measure q[2];\nc[0] = measure q[0];\n"
    )

    assert qasm2 == (
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[3];\ncreg c[3];\nx q[2];\n'
        "measure q[2] -> c[2];\nmeasure q[0] -> c[0];\n"
    )


def test_each_register_keeps_its_own_creg():
    """Two registers stay two ``creg`` declarations, in declaration order."""
    qasm2 = qasm3_to_qasm2(
        HEADER + "qubit[2] q;\nbit[1] a;\nbit[1] b;\na[0] = measure q[0];\nb[0] = measure q[1];\n"
    )

    assert "creg a[1];\ncreg b[1];" in qasm2
    assert "measure q[1] -> b[0];" in qasm2


def test_whole_register_measurement_and_scalar_declarations():
    """``c = measure q`` and ``bit c`` are expanded by unrolling into per-bit statements."""
    qasm2 = qasm3_to_qasm2(
        HEADER + "qubit[2] q;\nbit[2] c;\nqubit r;\nbit d;\nc = measure q;\nd = measure r;\n"
    )

    assert "qreg r[1];\ncreg d[1];" in qasm2
    assert "measure q[1] -> c[1];" in qasm2
    assert "measure r[0] -> d[0];" in qasm2


def test_gate_outside_qelib1_is_unrolled_into_qelib1_gates():
    """``cp`` has no OpenQASM 2 form on every backend, so unrolling decomposes it."""
    qasm2 = qasm3_to_qasm2(HEADER + "qubit[2] q;\nbit[2] c;\ncp(0.2) q[0], q[1];\nc = measure q;\n")

    assert "cp" not in qasm2
    assert "cx q[0], q[1];" in qasm2
    assert "creg c[2];" in qasm2


def test_custom_gates_are_unrolled_and_global_phase_dropped():
    """Gates outside ``qelib1.inc`` are decomposed, and ``gphase`` has no QASM 2 form."""
    qasm2 = qasm3_to_qasm2(
        HEADER + "gate g(t) a, b { rx(t) a; cx a, b; }\nqubit[2] q;\ng(0.5) q[0], q[1];\n"
        "gphase(0.1);\n"
    )

    assert "rx(0.5) q[0];\ncx q[0], q[1];" in qasm2
    assert "gate" not in qasm2.split("\n", 2)[2]
    assert "gphase" not in qasm2


def test_reset_and_barrier_pass_through():
    """Both statements read the same in OpenQASM 2."""
    qasm2 = qasm3_to_qasm2(HEADER + "qubit[2] q;\nreset q[0];\nbarrier q[0], q[1];\n")

    assert "reset q[0];\nbarrier q[0], q[1];" in qasm2


def test_exponent_literal_gains_the_decimal_point_qasm2_requires():
    """OpenQASM 2's real literal needs a decimal point, so ``1e-05`` becomes ``1.0e-05``."""
    qasm2 = qasm3_to_qasm2(HEADER + "qubit[1] q;\nrz(1e-05) q[0];\n")

    assert "rz(1.0e-05) q[0];" in qasm2


@pytest.mark.parametrize(
    "body",
    [
        "qubit[2] q;\nbit[1] c;\nc[0] = measure q[0];\nif (c[0]) { x q[1]; }\n",
        "qubit[1] q;\nmeasure q[0];\n",
        "bit[1] c;\nh $1;\nc[0] = measure $1;\n",
        "qubit[1] Q;\nh Q[0];\n",
        "qubit[1] _q;\nh _q[0];\n",
        "qubit[1] q;\nbit[1] rzz;\nrzz[0] = measure q[0];\n",
        "qubit[1] q;\nbit[1] exp;\nexp[0] = measure q[0];\n",
    ],
    ids=[
        "bit-condition",
        "measurement-without-target",
        "physical-qubit",
        "uppercase-name",
        "underscore-name",
        "gate-name",
        "keyword-name",
    ],
)
def test_statement_qasm2_cannot_express_raises(body):
    """The transpiler tries its next conversion path on ValueError."""
    with pytest.raises(ValueError, match="OpenQASM 2 cannot"):
        qasm3_to_qasm2(HEADER + body)


def test_transpiler_prefers_the_direct_conversion():
    """One hop beats the two through Cirq, which renamed ``c`` to ``m_c``."""
    path = ConversionGraph().find_shortest_conversion_path("qasm3", "qasm2")

    assert [conversion.__self__.source for conversion in path] == ["qasm3"]


def test_transpiler_falls_back_when_qasm2_cannot_express_the_program():
    """A bit-level condition still converts, through the Cirq path."""
    qasm2 = transpile(
        HEADER + "qubit[2] q;\nbit[2] c;\nh q[0];\nc[0] = measure q[0];\n"
        "if (c[0]) { x q[1]; }\nc[1] = measure q[1];\n",
        "qasm2",
    )

    assert qasm2.startswith("OPENQASM 2.0;")
    assert "if" in qasm2

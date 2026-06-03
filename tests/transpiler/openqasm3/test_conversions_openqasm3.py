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
Unit tests for OpenQASM 3 to pyQuil conversion.

"""

import pytest

try:
    import pyquil  # pylint: disable=unused-import

    from qbraid.interface import circuits_allclose
    from qbraid.transpiler.conversions.openqasm3.openqasm3_to_pyquil import openqasm3_to_pyquil
    from qbraid.transpiler.conversions.qasm3 import qasm3_to_cirq
    from qbraid.transpiler.exceptions import ProgramConversionError

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def test_openqasm3_to_pyquil_bell():
    """Bell circuit converts and matches unitary."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    h q[0];
    cx q[0], q[1];
    """
    result = openqasm3_to_pyquil(qasm)
    reference = qasm3_to_cirq(qasm)
    assert circuits_allclose(reference, result, strict_gphase=False)


def test_openqasm3_to_pyquil_parameterized():
    """Parameterized gates convert and match unitary."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    rx(0.5) q[0];
    rz(1.2) q[1];
    cp(0.3) q[0], q[1];
    """
    result = openqasm3_to_pyquil(qasm)
    reference = qasm3_to_cirq(qasm)
    assert circuits_allclose(reference, result, strict_gphase=False)


def test_openqasm3_to_pyquil_measurement():
    """Measurement produces a DECLARE + MEASURE."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    bit[2] c;
    h q[0];
    cx q[0], q[1];
    c[0] = measure q[0];
    c[1] = measure q[1];
    """
    result = openqasm3_to_pyquil(qasm)
    out = result.out()
    assert "DECLARE ro BIT[2]" in out
    assert out.count("MEASURE") == 2


def test_openqasm3_to_pyquil_malformed_raises():
    """Malformed QASM raises ProgramConversionError."""
    with pytest.raises(ProgramConversionError):
        openqasm3_to_pyquil("OPENQASM 3.0; this is not valid;")


def test_openqasm3_to_pyquil_unsupported_statement_raises():
    """A statement outside the supported set (e.g. reset) raises ProgramConversionError."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[1] q;
    reset q[0];
    """
    with pytest.raises(ProgramConversionError):
        openqasm3_to_pyquil(qasm)

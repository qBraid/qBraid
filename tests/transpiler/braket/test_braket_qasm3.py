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
Unit tests for converting Braket circuits to/from OpenQASM

"""
import textwrap

import numpy as np
import pytest
import qiskit
from braket.circuits import Circuit

from qbraid.interface import circuits_allclose
from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.conversions.braket import braket_to_qasm3
from qbraid.transpiler.conversions.qasm3 import qasm3_to_braket
from qbraid.transpiler.conversions.qiskit import qiskit_to_qasm3


def test_braket_to_qasm3_bell_circuit():
    """Test converting braket bell circuit to OpenQASM 3.0 string"""
    qasm_expected = """
    OPENQASM 3.0;
    bit[2] b;
    qubit[2] q;
    h q[0];
    cnot q[0], q[1];
    b[0] = measure q[0];
    b[1] = measure q[1];
    """

    qasm_expected_2 = """
    OPENQASM 3.0;
    bit[2] __bits__;
    qubit[2] __qubits__;
    h __qubits__[0];
    cnot __qubits__[0], __qubits__[1];
    __bits__[0] = measure __qubits__[0];
    __bits__[1] = measure __qubits__[1];
    """
    bell = Circuit().h(0).cnot(0, 1).measure(0).measure(1)
    qasm_out = braket_to_qasm3(bell).strip()
    qasm_expected = textwrap.dedent(qasm_expected).strip()
    qasm_expected_2 = textwrap.dedent(qasm_expected_2).strip()
    assert qasm_out in [qasm_expected, qasm_expected_2]


def test_braket_to_qasm3_bell_no_measurements():
    """Test converting braket circuit with no measurements to OpenQASM 3.0 string"""
    qasm_expected = """
    OPENQASM 3.0;
    bit[2] b;
    qubit[2] q;
    h q[0];
    cnot q[0], q[1];
    """

    qasm_expected_2 = """
    OPENQASM 3.0;
    bit[2] __bits__;
    qubit[2] __qubits__;
    h __qubits__[0];
    cnot __qubits__[0], __qubits__[1];
    """
    bell = Circuit().h(0).cnot(0, 1)
    qasm_out: str = braket_to_qasm3(bell).strip()
    qasm_expected = textwrap.dedent(qasm_expected).strip()
    qasm_expected_2 = textwrap.dedent(qasm_expected_2).strip()
    assert qasm_out in [qasm_expected, qasm_expected_2]


def test_braket_from_qasm3():
    """Test converting OpenQASM 3 string to braket circuit"""
    qasm = """
    OPENQASM 3.0;
    bit[2] b;
    qubit[2] q;
    rx(0.15) q[0];
    rx(0.3) q[1];
    """
    qasm = textwrap.dedent(qasm).strip()
    circuit_expected = Circuit().rx(0, 0.15).rx(1, 0.3)
    assert circuit_expected == qasm3_to_braket(qasm)


def test_braket_from_qasm3_physical_qubits():
    """Test converting OpenQASM 3 string with physical qubits to a braket circuit"""
    qasm = """
OPENQASM 3.0;
include "stdgates.inc";
gate prx(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(0) _gate_q_0;
  rx(pi/2) _gate_q_0;
  rz(0) _gate_q_0;
}
gate prx_0(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(pi/2) _gate_q_0;
  rx(pi) _gate_q_0;
  rz(-pi/2) _gate_q_0;
}
gate prx_1(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(0) _gate_q_0;
  rx(-pi/2) _gate_q_0;
  rz(0) _gate_q_0;
}
gate prx_2(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(pi/2) _gate_q_0;
  rx(-pi) _gate_q_0;
  rz(-pi/2) _gate_q_0;
}
gate prx_3(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(0) _gate_q_0;
  rx(-pi/2) _gate_q_0;
  rz(0) _gate_q_0;
}
gate prx_4(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(pi/2) _gate_q_0;
  rx(-2*pi) _gate_q_0;
  rz(-pi/2) _gate_q_0;
}
gate prx_5(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(0) _gate_q_0;
  rx(-pi/2) _gate_q_0;
  rz(0) _gate_q_0;
}
gate prx_6(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(pi/2) _gate_q_0;
  rx(pi/2) _gate_q_0;
  rz(-pi/2) _gate_q_0;
}
gate prx_7(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(0) _gate_q_0;
  rx(-pi/2) _gate_q_0;
  rz(0) _gate_q_0;
}
gate prx_8(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(pi/2) _gate_q_0;
  rx(-3.2994851870005952) _gate_q_0;
  rz(-pi/2) _gate_q_0;
}
gate prx_9(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(0) _gate_q_0;
  rx(-pi/2) _gate_q_0;
  rz(0) _gate_q_0;
}
gate prx_10(_gate_p_0, _gate_p_1) _gate_q_0 {
  rz(pi/2) _gate_q_0;
  rx(-7*pi/2) _gate_q_0;
  rz(-pi/2) _gate_q_0;
}
bit[2] meas;
prx(pi/2, 0) $0;
prx_0(pi, pi/2) $0;
prx_1(-pi/2, 0) $0;
prx(pi/2, 0) $0;
prx(pi/2, 0) $0;
prx_2(-pi, pi/2) $0;
prx_3(-pi/2, 0) $0;
prx(pi/2, 0) $0;
prx(pi/2, 0) $0;
prx_4(-2*pi, pi/2) $0;
prx_5(-pi/2, 0) $0;
prx(pi/2, 0) $1;
prx_6(pi/2, pi/2) $1;
prx_7(-pi/2, 0) $1;
prx(pi/2, 0) $1;
prx(pi/2, 0) $1;
prx_8(-3.2994851870005952, pi/2) $1;
prx_9(-pi/2, 0) $1;
prx(pi/2, 0) $1;
prx(pi/2, 0) $1;
prx_10(-7*pi/2, pi/2) $1;
barrier $0, $1;
meas[0] = measure $0;
meas[1] = measure $1;
    """
    qasm = textwrap.dedent(qasm).strip()
    circuit = qasm3_to_braket(qasm)
    assert isinstance(circuit, Circuit)


def test_qiskit_to_qasm3_to_braket():
    """Test converting Qiskit circuit to Braket via OpenQASM 3.0 for mapped gate defs"""
    qc = qiskit.QuantumCircuit(4)
    qc.cx(0, 1)
    qc.s(0)
    qc.sdg(1)
    qc.t(2)
    qc.tdg(3)
    qc.sx(0)
    qc.sxdg(1)
    qc.p(np.pi / 8, 3)
    qc.cp(np.pi / 4, 2, 3)

    qasm3_str = qiskit_to_qasm3(qc)
    circuit = qasm3_to_braket(qasm3_str)
    assert circuits_allclose(qc, circuit)


@pytest.mark.parametrize(
    "match_substring",
    ["PyQASM validation", "Transform"],
    ids=["pyqasm_validation_in_final_error", "transform_in_final_error"],
)
def test_qasm3_to_braket_prior_errors_included_in_final_error(match_substring):
    """Coverage: prior_errors (PyQASM validation and/or Transform) are included in QasmError

    Invalid QASM causes the first try (PyQASM) to raise; the second try (transform_notation
    -> replace_gate_names -> parse) also raises. The final QasmError message includes both.
    """
    invalid_qasm = "not valid openqasm"
    with pytest.raises(QasmError, match=f"Prior errors:.*{match_substring}"):
        qasm3_to_braket(invalid_qasm)


def test_qasm3_to_braket_error_includes_detail():
    """Verify that QasmError includes the specific failure reason from the Braket parser.

    The gate is deliberately one no QASM library will ever define. This test
    previously used `c3x`, relying on pyqasm leaving it alone so Braket's parser
    would reject it — but pyqasm 1.0.4 learned to decompose `c3x` during unroll,
    so the conversion started succeeding and the test broke. Any real-but-exotic
    gate is a moving target; a fake one is not. pyqasm's own rejection of the
    unknown gate is caught into `prior_errors`, the original program flows to
    Braket's parser, and its "not defined" detail must surface in the QasmError.
    """
    qasm_input = textwrap.dedent(
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        qubit[4] q;
        h q[0];
        notarealgate q[0], q[1];
        """
    ).strip()
    with pytest.raises(QasmError, match="notarealgate is not defined"):
        qasm3_to_braket(qasm_input)


@pytest.mark.parametrize(
    "delay_stmt",
    [
        "delay[100ns] q[0];",
        "delay[100dt] q[0];",
        "delay[20us] q[0];",
        "delay[100ns] q;",
    ],
    ids=["ns", "dt", "us", "whole_register"],
)
def test_qasm3_to_braket_delay_raises(delay_stmt):
    """Braket cannot represent a gate-level delay, so conversion must raise rather than
    drop it. Silently dropping produces a circuit that runs but measures the wrong thing.
    """
    qasm_input = textwrap.dedent(
        f"""
        OPENQASM 3.0;
        include "stdgates.inc";
        bit[1] c;
        qubit[1] q;
        x q[0];
        {delay_stmt}
        c[0] = measure q[0];
        """
    ).strip()
    with pytest.raises(QasmError, match="Delay instructions are not supported"):
        qasm3_to_braket(qasm_input)


def test_qasm3_to_braket_delay_in_verbatim_box_raises():
    """A delay nested inside a verbatim box must be caught too. Braket drops both the
    delay and the box on this path, so verbatim is not a workaround.
    """
    qasm_input = textwrap.dedent(
        """
        OPENQASM 3.0;
        bit[1] c;
        #pragma braket verbatim
        box{
        rx(1.5707963267948966) $0;
        delay[100ns] $0;
        }
        c[0] = measure $0;
        """
    ).strip()
    with pytest.raises(QasmError, match="Delay instructions are not supported"):
        qasm3_to_braket(qasm_input)


def test_qasm3_to_braket_no_delay_unaffected():
    """Programs without a delay convert as before."""
    qasm_input = textwrap.dedent(
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        bit[2] c;
        qubit[2] q;
        h q[0];
        cx q[0], q[1];
        c[0] = measure q[0];
        c[1] = measure q[1];
        """
    ).strip()
    assert qasm3_to_braket(qasm_input) == Circuit().h(0).cnot(0, 1).measure(0).measure(1)


def test_qasm3_to_braket_identifier_named_delay_unaffected():
    """An identifier that merely contains the substring 'delay' is not a delay
    instruction, and must not trip the delay check.
    """
    qasm_input = textwrap.dedent(
        """
        OPENQASM 3.0;
        include "stdgates.inc";
        qubit[1] delay_reg;
        x delay_reg[0];
        """
    ).strip()
    assert qasm3_to_braket(qasm_input) == Circuit().x(0)


def test_qasm3_to_braket_malformed_input_defers_downstream():
    """Malformed input is left to the downstream parsers, which report it in context --
    it must not be misreported as an (unsupported) delay instruction.
    """
    with pytest.raises(QasmError) as exc_info:
        qasm3_to_braket("delay this is not valid openqasm")
    assert "Delay instructions are not supported" not in str(exc_info.value)

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
Unit tests for qasm2/qasm3 to IonQDictType transpilation

"""
import importlib.util
import sys
from unittest.mock import Mock, patch

import openqasm3.ast
import pytest
from openqasm3.parser import parse

from qbraid.programs.gate_model.ionq import GateSet, InputFormat
from qbraid.programs.gate_model.qasm3 import OpenQasm3Program
from qbraid.programs.typer import IonQDictType, Qasm3StringType
from qbraid.transpiler.conversions.openqasm3.openqasm3_to_ionq import (
    _parse_gates,
    _register_offsets,
    extract_params,
    openqasm3_to_ionq,
)
from qbraid.transpiler.conversions.qasm2.qasm2_to_ionq import qasm2_to_ionq
from qbraid.transpiler.conversions.qasm3.qasm3_to_ionq import qasm3_to_ionq
from qbraid.transpiler.exceptions import ProgramConversionError


def test_ionq_device_extract_gate_data():
    """Test extracting gate data from a OpenQASM 2 program."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    x q[0];
    not q[1];
    y q[0];
    z q[0], q[1];
    rx(pi / 4) q[0];
    ry(pi / 2) q[0];
    rz(3 * pi / 4) q[0];
    h q[0];
    cx q[0], q[1];
    CX q[1], q[2];
    cnot q[2], q[0];
    ccx q[0], q[1], q[2];
    toffoli q[2], q[1], q[0];
    s q[0];
    sdg q[0];
    si q[0];
    id q[0];
    t q[0];
    tdg q[0];
    ti q[1];
    sx q[0];
    v q[1];
    sxdg q[0];
    vi q[1];
    swap q[0], q[1];
    """

    gate_data = [
        {"gate": "x", "target": 0},
        {"gate": "not", "target": 1},
        {"gate": "y", "target": 0},
        {"gate": "z", "target": 0},
        {"gate": "z", "target": 1},
        {"gate": "rx", "target": 0, "rotation": 0.7853981633974483},
        {"gate": "ry", "target": 0, "rotation": 1.5707963267948966},
        {"gate": "rz", "target": 0, "rotation": 2.356194490192345},
        {"gate": "h", "target": 0},
        {"gate": "cnot", "control": 0, "target": 1},
        {"gate": "cnot", "control": 1, "target": 2},
        {"gate": "cnot", "control": 2, "target": 0},
        {"gate": "cnot", "controls": [0, 1], "target": 2},
        {"gate": "cnot", "controls": [2, 1], "target": 0},
        {"gate": "s", "target": 0},
        {"gate": "si", "target": 0},
        {"gate": "si", "target": 0},
        {"gate": "t", "target": 0},
        {"gate": "ti", "target": 0},
        {"gate": "ti", "target": 1},
        {"gate": "v", "target": 0},
        {"gate": "v", "target": 1},
        {"gate": "vi", "target": 0},
        {"gate": "vi", "target": 1},
        {"gate": "swap", "targets": [0, 1]},
    ]
    expected = {
        "qubits": 3,
        "circuit": gate_data,
        "gateset": GateSet.QIS.value,
        "format": InputFormat.CIRCUIT.value,
    }

    actual = qasm2_to_ionq(qasm)

    assert actual == expected


def test_qasm2_to_ionq_measurements_raises():
    """Test that qasm2_to_ionq emits warning when the circuit contains measurements."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[1];
    creg c[1];
    x q[0];
    measure q[0] -> c[0];
    """
    with pytest.warns(
        UserWarning,
        match=(
            "Circuit contains measurement gates, which will be ignored "
            "during conversion to the IonQDictType"
        ),
    ):
        qasm2_to_ionq(qasm)


@pytest.fixture
def deutsch_jozsa_qasm3() -> Qasm3StringType:
    """Return a QASM 3.0 string for the DJ algorithm."""
    return """
    OPENQASM 3.0;
    include "stdgates.inc";

    gate hgate q { h q; }
    gate xgate q { x q; }

    const int[32] N = 4;
    qubit[4] q;
    qubit ancilla;

    def deutsch_jozsa(qubit[N] q_func, qubit[1] ancilla_q) {
    xgate ancilla_q;
    for int i in [0:N-1] { hgate q_func[i]; }
    hgate ancilla_q;
    for int i in [0:N-1] { cx q_func[i], ancilla_q; }
    for int i in [0:N-1] { hgate q_func[i]; }
    }

    deutsch_jozsa(q, ancilla);
    """


@pytest.fixture
def deutch_jozsa_qasm3_unrolled() -> Qasm3StringType:
    """Return an unrolled QASM 3.0 string for the DJ algorithm."""
    return """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[4] q;
    qubit[1] ancilla;
    x ancilla[0];
    h q[0];
    h q[1];
    h q[2];
    h q[3];
    h ancilla[0];
    cx q[0], ancilla[0];
    cx q[1], ancilla[0];
    cx q[2], ancilla[0];
    cx q[3], ancilla[0];
    h q[0];
    h q[1];
    h q[2];
    h q[3];
    """


@pytest.fixture
def deutch_jozsa_ionq() -> IonQDictType:
    """Return the expected IonQDictType for the DJ algorithm."""
    return {
        "format": InputFormat.CIRCUIT.value,
        "qubits": 5,
        "circuit": [
            {"gate": "x", "target": 4},
            {"gate": "h", "target": 0},
            {"gate": "h", "target": 1},
            {"gate": "h", "target": 2},
            {"gate": "h", "target": 3},
            {"gate": "h", "target": 4},
            {"gate": "cnot", "control": 0, "target": 4},
            {"gate": "cnot", "control": 1, "target": 4},
            {"gate": "cnot", "control": 2, "target": 4},
            {"gate": "cnot", "control": 3, "target": 4},
            {"gate": "h", "target": 0},
            {"gate": "h", "target": 1},
            {"gate": "h", "target": 2},
            {"gate": "h", "target": 3},
        ],
        "gateset": GateSet.QIS.value,
    }


@pytest.fixture
def ionq_native_gates_qasm() -> Qasm3StringType:
    """Return a QASM 3.0 using only IonQ native gates."""
    return """
    OPENQASM 3.0;
    qubit[3] q;
    ms(0,0,0) q[0], q[1];
    ms(-0.5,0.6,0.1) q[1], q[2];
    gpi(0) q[0];
    gpi2(0.2) q[1];
    """


@pytest.fixture
def ionq_native_gates_dict() -> IonQDictType:
    """Return an IonQDictType for a program using native gates."""
    return {
        "format": InputFormat.CIRCUIT.value,
        "gateset": GateSet.NATIVE.value,
        "qubits": 3,
        "circuit": [
            {"gate": "ms", "targets": [0, 1], "phases": [0, 0], "angle": 0.0},
            {"gate": "ms", "targets": [1, 2], "phases": [-0.5, 0.6], "angle": 0.1},
            {"gate": "gpi", "phase": 0, "target": 0},
            {"gate": "gpi2", "phase": 0.2, "target": 1},
        ],
    }


@pytest.mark.skipif(sys.version_info < (3, 11), reason="Requires Python 3.10 or higher")
def test_qasm3_to_ionq_for_loop_succeeds_without_pyqasm_dumps(
    deutsch_jozsa_qasm3, deutch_jozsa_ionq
):
    """Test that for-loop programs convert successfully even when the pyqasm.dumps
    fallback path in the qasm3_to_ionq wrapper is broken, because openqasm3_to_ionq
    now handles unrolling internally via module.unrolled_ast."""
    with patch(
        "qbraid.transpiler.conversions.qasm3.qasm3_to_ionq.pyqasm.dumps",
        side_effect=Exception("Mocked exception"),
    ):
        ionq_program = qasm3_to_ionq(deutsch_jozsa_qasm3)
        assert ionq_program == deutch_jozsa_ionq


def test_qasm3_to_ionq_deutch_jozsa(
    deutsch_jozsa_qasm3, deutch_jozsa_qasm3_unrolled, deutch_jozsa_ionq
):
    """Test transpiling the Deutsch-Jozsa algorithm from QASM 3.0 to IonQDictType."""
    pyqasm_installed = importlib.util.find_spec("pyqasm") is not None
    qasm_program = deutsch_jozsa_qasm3 if pyqasm_installed else deutch_jozsa_qasm3_unrolled
    ionq_program = qasm3_to_ionq(qasm_program)
    assert ionq_program == deutch_jozsa_ionq


def test_qasm3_to_ionq_deutch_jozsa_pyqasm_mocked(
    deutsch_jozsa_qasm3, deutch_jozsa_qasm3_unrolled, deutch_jozsa_ionq
):
    """Test Deutch-Jozsa conversion with mock pyqasm import and unroll."""
    mock_module = Mock()
    mock_module.unroll = Mock()
    mock_pyqasm = Mock()
    mock_pyqasm.dumps.return_value = deutch_jozsa_qasm3_unrolled

    mock_pyqasm.loads.return_value = mock_module

    with patch.dict("sys.modules", {"pyqasm": mock_pyqasm}):
        qasm_program = deutsch_jozsa_qasm3
        ionq_program = qasm3_to_ionq(qasm_program)
        assert ionq_program == deutch_jozsa_ionq


def test_qasm3_to_ionq_native_gates(ionq_native_gates_qasm, ionq_native_gates_dict):
    """Test transpiling a program using IonQ native gates to IonQDictType."""
    ionq_program = qasm3_to_ionq(ionq_native_gates_qasm)
    assert ionq_program["format"] == ionq_native_gates_dict["format"]
    assert ionq_program["qubits"] == ionq_native_gates_dict["qubits"]
    assert ionq_program["gateset"] == ionq_native_gates_dict["gateset"]
    assert ionq_program["circuit"] == ionq_native_gates_dict["circuit"]
    assert len(ionq_program) == 4


def test_qasm3_to_ionq_zz_native_gate():
    """Test transpiling a program containing the 'zz' native gate to IonQDictType."""
    qasm_program = """
    OPENQASM 3.0;
    qubit[2] q;
    zz(0.12) q[0], q[1];
    """
    expectd_ionq = {
        "format": InputFormat.CIRCUIT.value,
        "gateset": GateSet.NATIVE.value,
        "qubits": 2,
        "circuit": [
            {"gate": "zz", "targets": [0, 1], "angle": 0.12},
        ],
    }

    assert qasm3_to_ionq(qasm_program) == expectd_ionq


def test_openqasm3_to_ionq_bare_register_expands_to_all_qubits():
    """A gate applied to a whole register (no index) fans out across the register.

    Regression test for #864: the bare-register branch of ``openqasm3_to_ionq`` reads
    the register width from ``program_qubits``, which is empty until pyqasm populates
    ``_qubit_registers``. Every other test here indexes its qubits and so exercises the
    else-branch instead, leaving this expansion path uncovered even after the underlying
    defect was fixed. ``h q`` on a 3-qubit register must emit one gate per qubit.
    """
    qasm_program = """
    OPENQASM 3.0;
    qubit[3] q;
    h q;
    """
    expected_ionq = {
        "format": InputFormat.CIRCUIT.value,
        "gateset": GateSet.QIS.value,
        "qubits": 3,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "h", "target": 1},
            {"gate": "h", "target": 2},
        ],
    }

    assert openqasm3_to_ionq(parse(qasm_program)) == expected_ionq


def test_qasm2_to_ionq_multiple_registers():
    """Qubits in a later register are numbered after those in earlier registers.

    Regression test for #770: every register's qubits were emitted as if they started
    at 0, so ``cx q2[0], q2[1]`` landed on qubits 0 and 1 of ``q`` instead of 2 and 3.
    """
    qasm_program = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    x q[0];
    y q[0];

    qreg q2[2];
    cx q2[0], q2[1];
    h q2;
    cx q[1], q2[0];
    """
    expected_circuit = [
        {"gate": "x", "target": 0},
        {"gate": "y", "target": 0},
        {"gate": "cnot", "control": 2, "target": 3},
        {"gate": "h", "target": 2},
        {"gate": "h", "target": 3},
        {"gate": "cnot", "control": 1, "target": 2},
    ]

    ionq_program = qasm2_to_ionq(qasm_program)
    assert ionq_program["qubits"] == 4
    assert ionq_program["circuit"] == expected_circuit


def test_qasm3_to_ionq_multiple_registers():
    """Register offsets follow declaration order, including a const-sized register."""
    qasm_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    const int n = 3;
    qubit a;
    qubit[n] b;
    qubit[2] c;
    cx a, b[2];
    rz(0.5) c[1];
    """
    expected_circuit = [
        {"gate": "cnot", "control": 0, "target": 3},
        {"gate": "rz", "target": 5, "rotation": 0.5},
    ]

    ionq_program = qasm3_to_ionq(qasm_program)
    assert ionq_program["qubits"] == 6
    assert ionq_program["circuit"] == expected_circuit


def test_register_offsets_rejects_non_literal_size():
    """A register whose size pyqasm hasn't resolved (e.g. because an earlier
    statement failed to unroll) raises a clear ValueError instead of the
    AttributeError that fell out of reading '.value' off a non-literal size."""
    qasm_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] a;
    ms(0.1, 0.2, 0.3, 0.4) a[0], a[1];
    const int n = 2;
    qubit[n] b;
    h b[0];
    """
    with pytest.raises(ValueError, match="cannot determine the size of qubit register 'b'"):
        openqasm3_to_ionq(qasm_program)


def test_register_offsets_counts_an_unsized_register_as_one_qubit():
    """A bare `qubit b;` advances the offset by one when pyqasm has not sized it.

    Reaching this needs a register pyqasm never resolved -- here because an earlier
    statement failed to unroll -- so the declared size, not `program_qubits`, is what
    the offset is computed from. The `ms` gate below is the trigger, and its error is
    what surfaces; the offsets are computed before it.
    """
    qasm_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] a;
    ms(0.1, 0.2, 0.3, 0.4) a[0], a[1];
    qubit b;
    h b;
    """
    with pytest.raises(ValueError, match="Invalid number of parameters for the 'ms' gate"):
        openqasm3_to_ionq(qasm_program)


def test_register_offsets_orders_mixed_sized_and_unsized_registers():
    """Declaration order holds when sized and unsized registers are interleaved."""
    ast = parse('OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] a;\nqubit b;\nqubit[3] c;\n')

    assert _register_offsets(ast, {}) == {"a": 0, "b": 2, "c": 3}


def test_single_qubit_gate_rejects_unresolved_register_alias():
    """A single-qubit gate on an unresolved register must not be dropped.

    The name search fell through without a match, leaving the operand list empty, so
    the gate vanished and the converted circuit computed something different from the
    program with nothing to signal it. The multi-qubit branch already rejected this;
    the single-qubit one did not.
    """
    qasm_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[4] q;
    let a = q[0:1];
    h a;
    x q[3];
    """
    with pytest.raises(ValueError, match="qubit register 'a' used by gate 'h'"):
        openqasm3_to_ionq(qasm_program)


def test_single_qubit_gate_on_a_declared_register_still_expands():
    """The valid case is unaffected: a bare register broadcasts over its qubits."""
    qasm_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    qubit[2] r;
    h q;
    x r[1];
    """
    ionq_program = openqasm3_to_ionq(qasm_program)

    assert ionq_program["qubits"] == 4
    assert ionq_program["circuit"] == [
        {"gate": "h", "target": 0},
        {"gate": "h", "target": 1},
        {"gate": "x", "target": 3},
    ]


def test_multi_qubit_gate_rejects_unresolved_register_alias():
    """An operand naming a register with no matching QubitDeclaration -- an
    alias, in this case -- raises a clear ValueError instead of a KeyError."""
    qasm_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[4] q;
    let a = q[0:1];
    cx a[0], a[1];
    """
    with pytest.raises(ValueError, match="qubit register 'a' used by gate 'cx'"):
        openqasm3_to_ionq(qasm_program)


def test_multi_qubit_gate_rejects_bare_register_broadcast():
    """A 2+ qubit gate applied to whole registers with no index raises a clear
    ValueError instead of an AttributeError from indexing a bare Identifier."""
    qasm_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    qubit[2] r;
    cx q, r;
    """
    with pytest.raises(ValueError, match="without an index"):
        openqasm3_to_ionq(qasm_program)

    # The public qasm3_to_ionq wrapper recovers via its pyqasm-assisted retry,
    # which unrolls the broadcast into indexed gates before reconverting.
    ionq_program = qasm3_to_ionq(qasm_program)
    assert ionq_program["qubits"] == 4


@pytest.mark.parametrize(
    "qasm_code, error_message",
    [
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    ms(1.1,0,0) q[0], q[1];
    """,
            "Invalid phase value",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    ms(0,-1.5,0) q[0], q[1];
    """,
            "Invalid phase value",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    gpi(-6) q[0], q[1];
    """,
            "Invalid phase value",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    gpi2(3.0) q[0], q[1];
    """,
            "Invalid phase value",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    ms(0,0,0.26) q[0], q[1];
    """,
            "Invalid angle value",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    ms(0,0,-0.1) q[0], q[1];
    """,
            "Invalid angle value",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    zz(abc) q[0], q[1];
    """,
            "Invalid angle value 'abc'",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    gpi(0) q[1];
    zz(2*pi) q[0], q[1];
    """,
            "Invalid angle value '2 * pi'",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    cgpi2(0) q[0], q[1];
    zz(2*pi) q[0], q[1];
    """,
            "Invalid angle value '2 * pi'",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    zz(0.15) q[0], q[1];
    zz(3.0) q[0], q[1];
    """,
            "Invalid angle value '3.0'",
        ),
    ],
)
def test_qasm3_to_ionq_invalid_params(qasm_code, error_message):
    """Test that qasm3_to_ionq raises an error when the circuit contains invalid parameters."""
    with pytest.raises(ProgramConversionError) as excinfo:
        qasm3_to_ionq(qasm_code)
    assert error_message in str(excinfo.value)


@pytest.mark.parametrize(
    "qasm_code, ionq_dict",
    [
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    zz(0.45) q[0], q[1];
    """,
            {
                "qubits": 2,
                "circuit": [{"gate": "zz", "rotation": 0.45, "targets": [0, 1]}],
                "gateset": "qis",
                "format": "ionq.circuit.v0",
            },
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    zz(-0.9) q[0], q[1];
    """,
            {
                "qubits": 2,
                "circuit": [{"gate": "zz", "rotation": -0.9, "targets": [0, 1]}],
                "gateset": "qis",
                "format": "ionq.circuit.v0",
            },
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    zz(0.1) q[0], q[1];
    """,
            {
                "qubits": 2,
                "circuit": [{"gate": "zz", "angle": 0.1, "targets": [0, 1]}],
                "gateset": "native",
                "format": "ionq.circuit.v0",
            },
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    h q[0];
    zz(pi/16) q[0], q[1];
    """,
            {
                "qubits": 2,
                "circuit": [
                    {"gate": "h", "target": 0},
                    {"gate": "zz", "rotation": 0.19634954084936207, "targets": [0, 1]},
                ],
                "gateset": "qis",
                "format": "ionq.circuit.v0",
            },
        ),
    ],
)
def test_qasm3_to_ionq_zz_context(qasm_code, ionq_dict):
    """Test that qasm3_to_ionq correctly labels the gate parameter based on the value."""
    assert qasm3_to_ionq(qasm_code) == ionq_dict


@pytest.mark.parametrize(
    "qasm_code, error_message",
    [
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    gpi q[0];
    """,
            "Phase parameter is required",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[1] q;
    rz q[0];
    """,
            "Rotation parameter is required",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    crz q[0], q[1];
    """,
            "Rotation parameter is required",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    zz q[0], q[1];
    """,
            "Angle parameter is required",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[1] q;
    invalid_gate q[0];
    """,
            "Gate 'invalid_gate' not supported",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[3] q;
    ch q[0], q[1], q[2];
    """,
            "Invalid number of qubits",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[3] q;
    cnot q[0], q[1], q[2];
    """,
            "Invalid number of qubits",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[4] q;
    ccnot q[0], q[1], q[2], q[3];
    """,
            "Invalid number of qubits",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[3] q;
    cgpi2(0) q[0], q[1], q[3];
    """,
            "Invalid number of qubits",
        ),
        (
            """
    OPENQASM 3.0;
    qubit[2] q;
    cgpi q[0], q[1];
    """,
            "Phase parameter is required",
        ),
    ],
)
def test_openqasm3_to_ionq_value_errors(qasm_code, error_message):
    """Test that openqasm3_to_ionq raises an error when the circuit contains
    a gate that is missing required parameters or is not supported."""
    with pytest.raises(ValueError) as excinfo:
        openqasm3_to_ionq(qasm_code)
    assert error_message in str(excinfo.value)


def test_qasm3_to_ionq_mixed_gate_types_raises_value_error():
    """Test that qasm3_to_ionq raises an error when the circuit contains mixed gate types."""
    mixed_gate_qasm = """
    OPENQASM 3.0;
    qubit[2] q;
    h q[0];
    h q[1];
    gpi(0) q[0], q[1];
    """
    with pytest.raises(ProgramConversionError) as excinfo:
        qasm3_to_ionq(mixed_gate_qasm)
    assert "Cannot mix native and QIS gates in the same circuit." in str(excinfo.value)


def test_extract_params_index_error_caught():
    """Test that the extract_params returns empty list for non-parametric gates."""
    h_gate_qasm = """
    OPENQASM 3.0;
    qubit[1] q;
    h q[0];    
    """
    program = parse(h_gate_qasm)
    statement = program.statements[1]
    assert isinstance(statement, openqasm3.ast.QuantumGate)
    assert extract_params(statement) == []


@pytest.mark.parametrize(
    "program_text",
    [
        """
    OPENQASM 3.0;
    qubit[2] q;
    ms(0,0,0,0) q[0], q[1];
    """,
        """
    OPENQASM 3.0;
    qubit[2] q;
    ms q[0], q[1];
    """,
    ],
)
def test_ionq_ms_gate_wrong_number_params(program_text):
    """Test ValueError is raised when 'ms' gate has an invalid number of parameters."""
    program = OpenQasm3Program(program_text)

    with pytest.raises(ValueError) as excinfo:
        _ = _parse_gates(program)
    assert "Invalid number of parameters" in str(excinfo.value)


@pytest.fixture
def controlled_gates_qasm() -> Qasm3StringType:
    """Return a QASM 3.0 string containing various controlled gates."""
    return """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[5] q;

    cx q[0], q[4];
    cy q[1], q[4];
    cz q[2], q[4];
    crx(0.7853981633974483) q[3], q[4];
    cry(1.5707963267948966) q[3], q[4];
    crz(2.356194490192345) q[3], q[4];
    ch q[0], q[4];
    ccx q[0], q[1], q[4];
    """


@pytest.fixture
def controlled_gates_ionq() -> IonQDictType:
    """Return the expected IonQDictType for controlled gated circuit."""
    return {
        "format": InputFormat.CIRCUIT.value,
        "qubits": 5,
        "circuit": [
            {"gate": "cnot", "control": 0, "target": 4},
            {"gate": "y", "control": 1, "target": 4},
            {"gate": "z", "control": 2, "target": 4},
            {"gate": "rx", "control": 3, "target": 4, "rotation": 0.7853981633974483},
            {"gate": "ry", "control": 3, "target": 4, "rotation": 1.5707963267948966},
            {"gate": "rz", "control": 3, "target": 4, "rotation": 2.356194490192345},
            {"gate": "h", "control": 0, "target": 4},
            {"gate": "cnot", "controls": [0, 1], "target": 4},
        ],
        "gateset": GateSet.QIS.value,
    }


def test_qasm3_to_ionq_controlled_gates(controlled_gates_qasm, controlled_gates_ionq):
    """Test transpiling QASM 3.0 program containing various controlled gates to IonQDictType."""
    ionq_program = qasm3_to_ionq(controlled_gates_qasm)
    assert ionq_program == controlled_gates_ionq


@pytest.fixture
def controlled_gates_native_qasm() -> Qasm3StringType:
    """Return a QASM 3.0 string containing native controlled gates."""
    return """
    OPENQASM 3.0;
    include "stdgates.inc";
    // this declaration is required so that the pyqasm parser can correctly
    // identify the gate
    gate cgpi2(a) q1, q2 {
    }
    qubit[2] q;

    cgpi2(0.2) q[0], q[1];
    """


@pytest.fixture
def controlled_gates_native_ionq() -> IonQDictType:
    """Return the expected IonQDictType for circuit with native controlled gates."""
    return {
        "format": InputFormat.CIRCUIT.value,
        "qubits": 2,
        "circuit": [
            {"gate": "gpi2", "phase": 0.2, "control": 0, "target": 1},
        ],
        "gateset": GateSet.NATIVE.value,
    }


def test_qasm3_to_ionq_native_controlled_gates(
    controlled_gates_native_qasm, controlled_gates_native_ionq
):
    """Test transpiling QASM 3.0 program containing native controlled gates to IonQDictType."""
    ionq_program = qasm3_to_ionq(controlled_gates_native_qasm)
    assert ionq_program == controlled_gates_native_ionq


def test_openqasm3_to_ionq_for_loop_unrolled(deutsch_jozsa_qasm3, deutch_jozsa_ionq):
    """Test that openqasm3_to_ionq handles for-loop programs by using
    the unrolled AST when no top-level gate operations are found."""
    ionq_program = openqasm3_to_ionq(deutsch_jozsa_qasm3)
    assert ionq_program == deutch_jozsa_ionq


def test_openqasm3_to_ionq_no_gates_error_message():
    """Test that a program with no gate operations produces a descriptive error."""
    qasm_no_gates = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    """
    with pytest.raises(ProgramConversionError, match="No gate operations found"):
        openqasm3_to_ionq(qasm_no_gates)


def test_parse_gates_uses_unrolled_ast_when_no_top_level_gates():
    """Test that _parse_gates falls back to unrolled_ast when
    original_program has no top-level QuantumGate statements."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    h q[0];
    cx q[0], q[1];
    """
    program = OpenQasm3Program(qasm)

    # Build an unrolled AST that has gate operations
    unrolled = parse(qasm)

    # Replace original_program with one that has no QuantumGate statements
    empty_original = openqasm3.ast.Program(statements=[], version="3.0")
    program._module._original_program = empty_original
    program._module._unrolled_ast = unrolled

    gates = _parse_gates(program)
    assert len(gates) > 0


@pytest.mark.parametrize(
    "gate_line",
    ["rx(0.5) $0;", "cx $0, $1;", "h q[0];\n    ry(0.25) $1;"],
    ids=["single-qubit", "two-qubit", "alongside-a-register"],
)
def test_openqasm3_to_ionq_rejects_hardware_qubits(gate_line):
    """Hardware qubits cannot be expressed in IonQ's logical-register format.

    qiskit>=2 emits these once a circuit is laid out on a backend's physical qubits. They
    were previously an AttributeError on a multi-qubit gate, and silently dropped the gate
    on a single-qubit one.
    """
    qasm = f"""
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    {gate_line}
    """
    with pytest.raises(ValueError) as excinfo:
        openqasm3_to_ionq(qasm)
    assert "is not supported by the IonQ format" in str(excinfo.value)

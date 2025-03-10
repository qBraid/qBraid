# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

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
            {"gate": "x", "target": 0},
            {"gate": "h", "target": 0},
            {"gate": "h", "target": 1},
            {"gate": "h", "target": 2},
            {"gate": "h", "target": 3},
            {"gate": "h", "target": 0},
            {"gate": "cnot", "control": 0, "target": 0},
            {"gate": "cnot", "control": 1, "target": 0},
            {"gate": "cnot", "control": 2, "target": 0},
            {"gate": "cnot", "control": 3, "target": 0},
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
def test_qasm3_to_ionq_no_pyqasm(deutsch_jozsa_qasm3):
    """Test transpiling the Deutsch-Jozsa algorithm from QASM 3.0 to IonQDictType."""
    with patch(
        "qbraid.transpiler.conversions.qasm3.qasm3_to_ionq.pyqasm.dumps",
        side_effect=Exception("Mocked exception"),
    ):
        with pytest.raises(ProgramConversionError) as excinfo:
            qasm3_to_ionq(deutsch_jozsa_qasm3)
        assert "Failed to parse gate data from OpenQASM string." in str(excinfo.value)


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


@pytest.mark.skip(reason="To validate in pyqasm through definition of ms gate")
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

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
Unit tests for qasm2 to IonQDictType transpilation

"""
from unittest.mock import patch

import pytest

from qbraid.transpiler.conversions.qasm2.qasm2_to_ionq import qasm2_to_ionq
from qbraid.transpiler.conversions.qasm3.qasm3_to_ionq import qasm3_to_ionq
from qbraid.transpiler.exceptions import CircuitConversionError


def test_ionq_device_extract_gate_data():
    """Test extracting gate data from a OpenQASM 2 program."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    x q[0];
    not q[1];
    y q[0];
    z q[0], q[1];
    rx(pi / 4) q[0];
    ry(pi / 2) q[0];
    rz(3 * pi / 4) q[0];
    h q[0];
    h q;
    cx q[0], q[1];
    CX q[1], q[2];
    cnot q[2], q[0];
    ccx q[0], q[1], q[2];
    toffoli q[2], q[1], q[0];
    s q[0];
    sdg q[0];
    si q[0];
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
        {"gate": "h", "target": 0},
        {"gate": "h", "target": 1},
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
    expected = {"qubits": 2, "circuit": gate_data, "gateset": "qis"}

    actual = qasm2_to_ionq(qasm)

    assert actual == expected


def test_qasm2_to_ionq_measurements_raises():
    """Test that qasm2_to_ionq raises an error when the circuit contains measurements."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[1];
    creg c[1];
    x q[0];
    measure q[0] -> c[0];
    """
    with pytest.raises(ValueError) as exc_info:
        qasm2_to_ionq(qasm)
    assert "Circuits with measurements are not supported by the IonQDictType" in str(exc_info.value)


@pytest.fixture
def qasm3_program() -> str:
    """Return a simple QASM3 program."""
    return "OPENQASM 3; qubit q[2]; cx q[0], q[1];"


def test_qasm3_to_ionq_import_error(qasm3_program):
    """Test qasm3_to_ionq when the pyqasm import fails."""

    pytest.importorskip("pyqasm")

    with patch(
        "qbraid.transpiler.conversions.qasm2.qasm2_to_ionq.qasm_to_ionq"
    ) as mock_qasm_to_ionq:
        mock_qasm_to_ionq.side_effect = Exception("Initial conversion failed")

        with patch("pyqasm.unroll", side_effect=ImportError("pyqasm not available")):
            with pytest.raises(CircuitConversionError) as exc_info:
                qasm3_to_ionq(qasm3_program)

            assert "Please install the 'ionq' extra" in str(exc_info.value)


def test_qasm3_to_ionq_final_conversion_failure(qasm3_program):
    """Test qasm3_to_ionq when both initial and final conversion attempts fail."""

    pytest.importorskip("pyqasm")

    with patch(
        "qbraid.transpiler.conversions.qasm2.qasm2_to_ionq.qasm_to_ionq"
    ) as mock_qasm_to_ionq:
        mock_qasm_to_ionq.side_effect = Exception("Initial conversion failed")

        with patch("pyqasm.unroll", return_value=qasm3_program):
            mock_qasm_to_ionq.side_effect = Exception("Final conversion failed")

            with pytest.raises(CircuitConversionError) as exc_info:
                qasm3_to_ionq(qasm3_program)

            assert "Failed to convert QASM3 to IonQ" in str(exc_info.value)

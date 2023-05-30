# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

import os

from qiskit.qasm3 import loads

from qbraid.interface.qbraid_qasm.circuits import qasm_bell, qasm_shared15
from qbraid.interface.qbraid_qasm.tools import (
    convert_to_qasm_3,
    qasm_depth,
    qasm_num_qubits,
    qasm_qubits,
)


def test_qasm_qubits():
    """test calculate qasm qubit"""

    assert qasm_qubits(qasm_bell()) == ["qreg q[2];"]
    assert qasm_qubits(qasm_shared15()) == ["qreg q[4];"]


def test_qasm_num_qubits():
    assert qasm_num_qubits(qasm_bell()) == 2
    assert qasm_num_qubits(qasm_shared15()) == 4


def test_qasm_depth():
    """test calcualte qasm depth"""
    assert qasm_depth(qasm_bell()) == 2
    assert qasm_depth(qasm_shared15()) == 22


def _check_output(output, expected):
    actual_circuit = loads(output)
    expected_circuit = loads(expected)
    assert actual_circuit == expected_circuit


def test_convert_to_qasm_3():
    """test the conversion of qasm 2 to 3"""
    lib_dir = os.path.dirname(os.path.dirname(__file__)) + "/qasm_lib"
    gate_def_qasm3 = open(
        os.path.join(lib_dir, "qelib_qasm3.qasm"), mode="r", encoding="utf-8"
    ).read()

    # 1. qubit statement conversion
    test_qregs = """OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[1] ;
    qreg qubits  [10]   ;
    creg c[1];
    creg bits   [12]   ;
    """
    test_qregs_expected = f"""OPENQASM 3.0;
    include "stdgates.inc";
    {gate_def_qasm3}
    qubit[1] q;
    qubit[10] qubits;
    bit[1] c;
    bit[12] bits;"""

    _check_output(convert_to_qasm_3(test_qregs), test_qregs_expected)

    # 2. Measure statement conversion
    test_measure = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    measure q->c;
    measure q[0] -> c[1];
    """

    test_measure_expected = f"""
    OPENQASM 3.0;
    include "stdgates.inc";
    {gate_def_qasm3}
    qubit[2] q;
    bit[2] c;
    c = measure q;
    c[1] = measure q[0];
    """
    _check_output(convert_to_qasm_3(test_measure), test_measure_expected)

    # 3. Opaque comment conversion
    test_opaque = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    opaque custom_gate (a,b,c) p,q,r;
    """

    test_opaque_expected = f"""
    OPENQASM 3.0;
    include "stdgates.inc";
    {gate_def_qasm3}
    qubit[2] q;
    bit[2] c;
    // opaque custom_gate (a,b,c) p,q,r;
    """

    _check_output(convert_to_qasm_3(test_opaque), test_opaque_expected)

    # 4. std header change
    test_header = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[1];
    """

    test_header_expected = f"""
    OPENQASM 3.0;
    include "stdgates.inc";
    {gate_def_qasm3}
    qubit[1] q;
    """
    _check_output(convert_to_qasm_3(test_header), test_header_expected)

    # 5. Unsupported gate conversion
    test_unsupported = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    cu1(0.5) q[0], q[1];
    cu3(1,2,3) q[0], q[1];
    """
    test_unsupported_expected = f"""
    OPENQASM 3.0;   
    include "stdgates.inc";
    {gate_def_qasm3}
    qubit[2] q;
    bit[2] c;
    cu1(0.5) q[0], q[1];
    cu3(1, 2, 3) q[0], q[1];
    """
    _check_output(convert_to_qasm_3(test_unsupported), test_unsupported_expected)

    # 6. Fully random test
    # correct = 0
    # for _ in range(100):
    #     circuit = random_circuit("qiskit")
    #     qasm2_str = circuit.qasm()
    #     qasm3_str = convert_to_qasm_3(qasm2_str)
    #     circuit_test = loads(qasm3_str)
    #     print(circuit.draw())
    #     print(circuit_test.draw())
    #     eq = circuits_allclose(circuit, circuit_test)
    #     if eq:
    #         print("Correct!")
    #     assert eq

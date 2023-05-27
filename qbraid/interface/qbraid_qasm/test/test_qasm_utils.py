# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

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
    for line1, line2 in zip(output.splitlines(), expected.splitlines()):
        assert line1.strip() == line2.strip()


def test_convert_to_qasm_3():
    """test the conversion of qasm 2 to 3"""

    # 1. qubit statement conversion
    test_qregs = """OPENQASM 2.0;
    qreg q[1] ;
    qreg qubits  [10]   ;
    creg c[1];
    creg bits   [12]   ;
    """
    test_qregs_expected = """OPENQASM 3.0;
    qubit[1] q;
    qubit[10] qubits;
    bit[1] c;
    bit[12] bits;"""

    _check_output(convert_to_qasm_3(test_qregs), test_qregs_expected)

    # 2. Measure statement conversion
    test_measure = """
    OPENQASM 2.0;
    qreg q[2];
    creg c[2];
    measure q->c;
    measure q[0] -> c[1];
    """

    test_measure_expected = """
    OPENQASM 3.0;
    qubit[2] q;
    bit[2] c;
    c = measure q;
    c[1] = measure q[0];
    """
    _check_output(convert_to_qasm_3(test_measure), test_measure_expected)

    # 3. Opaque comment conversion
    test_opaque = """
    OPENQASM 2.0;
    qreg q[2];
    creg c[2];
    opaque custom_gate (a,b,c) p,q,r;
    """

    test_opaque_expected = """
    OPENQASM 3.0;
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

    test_header_expected = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[1] q;
    """
    _check_output(convert_to_qasm_3(test_header), test_header_expected)

    # 5. Fully random test
    test_random = """
    OPENQASM 2.0;
    include "qelib1.inc";
    gate r(param0,param1) q0 { u3(3.1008262509080406,4.42985566593216,-4.42985566593216) q0; }
    qreg q[3];
    creg c[3];
    cy q[2],q[1];
    s q[0];
    cp(3.0004583704185523) q[2],q[0];
    t q[1];
    crz(4.1306355067715455) q[2],q[0];
    rz(0.8430458524794254) q[1];
    cy q[1],q[2];
    u(4.406951880713489,5.860482620731477,1.4150079480777737) q[0];
    cu(1.101924061832913,5.126072002075184,5.423867802047752,0.9224141552349424) q[2],q[0];
    r(3.1008262509080406,6.0006519927270565) q[1];
    swap q[2],q[1];
    u1(4.917501631124593) q[0];
    measure q[0] -> c[0];
    measure q[1] -> c[1];
    measure q[2] -> c[2];
    """

    test_random_expected = """ 
    OPENQASM 3.0;
    include "stdgates.inc";
    gate r(param0,param1) q0 { u3(3.1008262509080406,4.42985566593216,-4.42985566593216) q0; }
    qubit[3] q;
    bit[3] c;
    cy q[2],q[1];
    s q[0];
    cp(3.0004583704185523) q[2],q[0];
    t q[1];
    crz(4.1306355067715455) q[2],q[0];
    rz(0.8430458524794254) q[1];
    cy q[1],q[2];
    u(4.406951880713489,5.860482620731477,1.4150079480777737) q[0];
    cu(1.101924061832913,5.126072002075184,5.423867802047752,0.9224141552349424) q[2],q[0];
    r(3.1008262509080406,6.0006519927270565) q[1];
    swap q[2],q[1];
    u1(4.917501631124593) q[0];
    c[0] = measure q[0];
    c[1] = measure q[1];
    c[2] = measure q[2];
    """

    _check_output(convert_to_qasm_3(test_random), test_random_expected)

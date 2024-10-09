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
Unit tests for qbraid.programs.qasm.OpenQasm3Program

"""
import numpy as np
import pytest
from qiskit.qasm3 import dumps, loads

from qbraid.interface.random.qasm3_random import _qasm3_random
from qbraid.interface.random.qiskit_random import _qiskit_random
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.qasm import OpenQasm3Program, expression_value
from qbraid.programs.registry import unregister_program_type
from qbraid.transpiler.conversions.qasm2.qasm2_to_qasm3 import _get_qasm3_gate_defs

from ..fixtures.qasm3.circuits import qasm3_bell, qasm3_shared15

gate_def_qasm3 = _get_qasm3_gate_defs()


def test_qasm_qubits():
    """Test getting QASM qubits"""

    assert OpenQasm3Program(qasm3_bell()).qubits == [("q", 2)]
    assert OpenQasm3Program(qasm3_shared15()).qubits == [("q", 4)]


def test_qasm3_num_qubits():
    """Test calculating number of qubits in qasm3 circuit"""
    num_qubits = np.random.randint(2, 10)
    depth = np.random.randint(1, 4)
    qiskit_circuit = _qiskit_random(num_qubits=num_qubits, depth=depth)
    qasm3_str = dumps(qiskit_circuit)
    assert OpenQasm3Program(qasm3_str).num_qubits == num_qubits


def test_qasm3_depth_alternate_qubit_syntax():
    """Test calculating qasm depth of qasm3 circuit"""
    qasm3_str = """OPENQASM 3.0;
bit[1] __bits__;
qubit[1] __qubits__;
h __qubits__[0];
__bits__[0] = measure __qubits__[0];"""
    assert OpenQasm3Program(qasm3_str).depth == 2


def _check_output(output, expected):
    actual_circuit = loads(output)
    expected_circuit = loads(expected)
    assert actual_circuit == expected_circuit


@pytest.mark.parametrize(
    "num_qubits, depth, max_operands, seed, measure",
    [
        (
            None,
            None,
            None,
            None,
            False,
        ),  # Test case 1: Generate random circuit with default parameters
        (3, 3, 3, 42, False),  # Test case 2: Generate random circuit with specified parameters
        (None, None, None, None, True),  # Test case 3: Generate random circuit with measurement
    ],
)
def test_qasm3_random(num_qubits, depth, max_operands, seed, measure):
    """Test random circuit generation using _qasm_random"""

    circuit = _qasm3_random(
        num_qubits=num_qubits, depth=depth, max_operands=max_operands, seed=seed, measure=measure
    )
    assert OpenQasm3Program(circuit).num_qubits >= 1
    if num_qubits is not None:
        assert OpenQasm3Program(circuit).num_qubits == num_qubits


def test_qasm3_random_with_known_seed():
    """Test generating random OpenQASM 3 circuit from known seed"""
    circuit = _qasm3_random(num_qubits=3, depth=3, max_operands=3, seed=42, measure=True)
    assert OpenQasm3Program(circuit).num_qubits == 3

    out__expected = """
// Random Circuit generated by qBraid
OPENQASM 3.0;
include "stdgates.inc";
/*
    seed = 42
    num_qubits = 3
    depth = 3
    max_operands = 3
*/
qubit[3] q;
bit[3] c;
y q[0];
crx(5.3947298351621535) q[1],q[2];
cz q[0],q[2];
t q[1];
cp(0.8049616944763924) q[1],q[2];
u1(2.829858307545725) q[0];
c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];

"""
    _check_output(circuit, out__expected)


def test_populate_idle_qubits_qasm3_small():
    """Test that remove_idle_qubits for qasm3 string"""
    qasm3_str = """
OPENQASM 3;
include "stdgates.inc";
qubit[4] q;
h q[1];
cx q[1], q[3];
"""
    qprogram = OpenQasm3Program(qasm3_str)
    qprogram.populate_idle_qubits()
    contig_qasm3_str = qprogram.program
    assert contig_qasm3_str == qasm3_str + """i q[0];\ni q[2];\n"""


def test_populate_idle_qubits_qasm3():
    """Test conversion of qasm3 to contiguous qasm3"""
    qasm_test = """
    OPENQASM 3.0;
    gate custom q1, q2, q3{
        x q1;
        y q2;
        z q3;
    }
    qreg q1[2];
    qubit[2] q2;
    qubit[3] q3;
    qubit q4;
    
    x q1[0];
    y q2[0];
    z q3;
    """

    qasm_expected = qasm_test + """i q1[1];\ni q2[1];\ni q4[0];\n"""

    qprogram = OpenQasm3Program(qasm_test)
    qprogram.populate_idle_qubits()
    assert qprogram.program == qasm_expected


def test_remove_idle_qubits_qasm3_small():
    """Test that remove_idle_qubits for qasm3 string"""
    qasm3_str = """
OPENQASM 3;
include "stdgates.inc";
qubit[4] q;
h q[1];
cx q[1], q[3];
"""
    qprogram = OpenQasm3Program(qasm3_str)
    qprogram.remove_idle_qubits()
    assert qprogram.num_qubits == 2


def test_remove_idle_qubits_qasm3():
    """Test conversion of qasm3 to compressed contiguous qasm3"""
    qasm_test = """
    OPENQASM 3.0;
    gate custom q1, q2, q3{
        x q1;
        y q2;
        z q3;
    }
    qreg q1[2];
    qubit[2] q2;
    qubit[3] q3;
    qubit q4;
    qubit[5]   q5;
    qreg qr[3];
    
    x q1[0];
    y q2[1];
    z q3;
    
    
    qubit[3] q6;
    
    cx q6[1], q6[2];
    """

    qasm_expected = """
    OPENQASM 3.0;
    gate custom q1, q2, q3{
        x q1;
        y q2;
        z q3;
    }
    qreg q1[1];
    qubit[1] q2;
    qubit[3] q3;
    
    
    
    
    x q1[0];
    y q2[0];
    z q3;
    
    
    qubit[2] q6;
    
    cx q6[0], q6[1];
    """

    qprogram = OpenQasm3Program(qasm_test)
    qprogram.remove_idle_qubits()
    assert qprogram.program == qasm_expected


def test_qasm3_num_qubits_alternate_synatx():
    """Test calculating num qubits for qasm3 syntax edge-case"""
    qasm3_str = """
OPENQASM 3;
include "stdgates.inc";
qubit _qubit0;
qubit _qubit1;
h _qubit0;
cx _qubit0, _qubit1;
"""
    qprogram = OpenQasm3Program(qasm3_str)
    assert qprogram.num_qubits == 2


def test_qasm3_num_clbits():
    """Test calculating num classical bits for qasm3"""
    qasm3_str = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""
    qprogram = OpenQasm3Program(qasm3_str)
    assert qprogram.num_clbits == 2
    assert qprogram.clbits == [("c", 2)]


def test_reverse_qubit_order():
    """Test the reverse qubit ordering function"""
    qasm_str = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    qubit[4] q2;
    qubit q3;

    cnot q[0], q[1];
    cnot q2[0], q2[1];
    x q2[3];
    cnot q2[0], q2[2];
    x q3[0];
    """

    program = OpenQasm3Program(qasm_str)
    program.reverse_qubit_order()
    reverse_qasm = program.program

    expected_qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    qubit[4] q2;
    qubit q3;

    cnot q[1], q[0];
    cnot q2[3], q2[2];
    x q2[0];
    cnot q2[3], q2[1];
    x q3[0];
    """
    assert reverse_qasm == expected_qasm


def test_apply_empty_qubit_mapping():
    """Test applying empty qubit mapping"""
    qasm = qasm3_bell()
    program = OpenQasm3Program(qasm)
    program.apply_qubit_mapping({})
    assert program.program == qasm


def test_remap_qubit_order():
    """Test the remapping of qubits in qasm string"""
    qubit_mapping = {"q1": {0: 1, 1: 0}, "q2": {0: 2, 1: 0, 2: 1}}
    qasm_str = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q1;
    qubit[3] q2;
    
    cnot q1[1], q1[0];
    cnot q2[2], q2[1];
    x q2[0];
    """

    program = OpenQasm3Program(qasm_str)
    program.apply_qubit_mapping(qubit_mapping)
    remapped_qasm = program.program

    expected_qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q1;
    qubit[3] q2;
    
    cnot q1[0], q1[1];
    cnot q2[1], q2[0];
    x q2[2];
    """
    assert expected_qasm == remapped_qasm


def test_incorrect_remapping():
    """Test that incorrect remapping raises error"""
    reg_not_there_mapping = {"q2": {0: 2, 1: 0, 2: 1}}
    incomplete_reg_mapping = {"q1": {0: 1, 1: 0}, "q2": {0: 2, 1: 0}}
    out_of_bounds_mapping = {"q1": {0: 1, 1: 2}, "q2": {0: 2, 1: 0, 3: 1}}

    qasm_str = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q1;
    qubit[3] q2;
    
    cnot q1[1], q1[0];
    cnot q2[2], q2[1];
    x q2[0];
    """

    with pytest.raises(ValueError):
        OpenQasm3Program(qasm_str).apply_qubit_mapping(reg_not_there_mapping)

    with pytest.raises(ValueError):
        OpenQasm3Program(qasm_str).apply_qubit_mapping(incomplete_reg_mapping)

    with pytest.raises(ValueError):
        OpenQasm3Program(qasm_str).apply_qubit_mapping(out_of_bounds_mapping)


def test_replace_reset():
    """Test replacing reset gate in qasm3 string"""
    qasm_input = """
OPENQASM 3;
include "stdgates.inc";
qubit q0;
qubit q1;
bit c0;
bit c1;
reset q0;
h q1;
cx q0, q1;
reset q1;
measure q1 -> c1;
    """

    expected_output = """
OPENQASM 3;
include "stdgates.inc";
qubit q0;
qubit q1;
bit c0;
bit c1;
measure q0 -> c0;
if (c0 == 1) x q0;
h q1;
cx q0, q1;
measure q1 -> c1;
if (c1 == 1) x q1;
measure q1 -> c1;
    """

    program = OpenQasm3Program(qasm_input)
    program.replace_reset_with_ops()
    assert program.program == expected_output


def test_qasm3_depth_sparse_operations():
    """Test calculating depth of qasm3 circuit with sparse operations"""
    qasm = """
OPENQASM 3.0;
bit[2] b;
qubit[2] q;
s q[0];
iswap q[0], q[1];
barrier;
z q[1];
    """
    qprogram = OpenQasm3Program(qasm)
    assert qprogram.depth == 3


def test_qasm3_depth_measurement_direct():
    """Test calculating depth of qasm3 circuit with direct measurements"""
    qasm = """
OPENQASM 3.0;
bit[2] b;
qubit[2] q;
s q[0];
iswap q[0], q[1];
z q[1];
b[0] = measure q[0];
b[1] = measure q[1];
    """
    qprogram = OpenQasm3Program(qasm)
    assert qprogram.depth == 4


def test_qasm3_depth_measurement_indirect():
    """Test calculating depth of qasm3 circuit with indirect measurements"""
    qasm = """
OPENQASM 3.0;
include "stdgates.inc";
bit[3] c;
qubit[3] q;
cry(4.2051581759108885) q[1], q[2];
x q[0];
cu(3.477667891331647, 4.2539794092334375, 3.436930389872277, 5.115111057204699) q[1], q[2];
h q[0];
rx(5.917500589065494) q[1];
c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];
    """
    qprogram = OpenQasm3Program(qasm)
    assert qprogram.depth == 4


def test_raise_program_type_error():
    """Test that initializing OpenQasm3Program with an invalid type raises ProgramTypeError."""
    try:
        with pytest.raises(ProgramTypeError):
            OpenQasm3Program(42)
    finally:
        unregister_program_type("int")


def test_replace_reset_with_ops():
    """Test replacing reset gate with operations in qasm3 string"""
    expected_qasm = """
OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;

measure q[0] -> c0;
if (c0 == 1) x q[0];
"""
    qasm = """
OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;

reset q[0];
"""
    qprogram = OpenQasm3Program(qasm)
    qprogram.replace_reset_with_ops()
    assert qprogram.program == expected_qasm


def test_validate_qubit_mapping_fail():
    """Test that invalid qubit mapping raises ValueError"""
    program = """
OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
"""

    qubit_decls = [("q", 1)]
    qubit_mapping = {"q": 0}

    qprogram = OpenQasm3Program(program)
    with pytest.raises(ValueError):
        qprogram._validate_qubit_mapping(qubit_decls, qubit_mapping)

    qubit_mapping = {"q": {1: 1}}
    with pytest.raises(ValueError):
        qprogram._validate_qubit_mapping(qubit_decls, qubit_mapping)

    qubit_decls = [("q", 2)]
    qubit_mapping = {"q": {0: 1, 1: 1}}

    with pytest.raises(ValueError):
        qprogram._validate_qubit_mapping(qubit_decls, qubit_mapping)


def test_get_unused_qubits():
    """Test getting unused qubits in qasm3 string"""
    program = """
OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;

h q[0];
"""
    qprogram = OpenQasm3Program(program)
    assert qprogram._get_unused_qubit_indices() == {"q": set()}


@pytest.mark.parametrize(
    "program, expected_depth",
    [
        (
            """
OPENQASM 3.0;
include "stdgates.inc";
         
qubit[2] q;
qubit[2] r;
qubit[2] s;
         
h q[0];
h q[1];
h r[0];
""",
            1,
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";

qreg q[2];
creg c[2];

h q[0];
cx q[0], q[1];
h q;

measure q -> c;
     """,
            4,
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";

qreg q[2];

reset q;
reset q[0];
""",
            2,
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";

qreg q[2];

h q[0];
h q[0];
h q[0];
h q[0];

barrier q;

h q[1];
""",
            5,
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";

qreg q[2];
creg c[2];

h q[0];
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];

if (c==1) x q[0];
""",
            4,
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";

qreg q[2];
creg c[2];

h q[0];
cx q[0], q[1];
measure q[0] -> c[0];

if (c==1) measure q[1] -> c[1];
""",
            4,
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";
qreg q1[3];
qreg q2[3];
creg c1[3];
creg c2[3];

gate big_gate a1, a2, a3, b1, b2, b3
{
    h a1;
}
x q1[0];
barrier q1;
big_gate q1[0],q1[1],q1[2],q2[0],q2[1],q2[2];
x q1[0];
measure q1 -> c1;
if(c1==1) x q2[0];
if(c1==2) x q2[2];
if(c1==3) x q2[1];
measure q2 -> c2;
""",
            8,
        ),
    ],
)
def test_qasm3_depth(program, expected_depth):
    """Test calculating depth of qasm3 circuit"""
    qprogram = OpenQasm3Program(program)
    assert qprogram.depth == expected_depth


def test_expression_value_raises():
    """Test that expression_value raises ValueError for invalid expression"""
    with pytest.raises(ValueError):
        expression_value(0)

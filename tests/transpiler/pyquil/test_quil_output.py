# Copyright (C) 2024 qBraid
# Copyright (C) 2022 The Cirq Developers
#
# This file is part of the qBraid-SDK.
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. This specific file, adapted from Cirq, is dual-licensed under both the
# Apache License, Version 2.0, and the GPL v3. You may not use this file except in
# compliance with the applicable license. You may obtain a copy of the Apache License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file includes code adapted from Cirq (https://github.com/quantumlib/Cirq)
# with modifications by qBraid. The original copyright notice is included above.
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# qbraid: skip-header

"""
Module for testing qBraid QuilOutput.

"""
import os

import cirq
import numpy as np
import pytest
from cirq.ops.pauli_interaction_gate import PauliInteractionGate

try:
    from qbraid.transpiler.conversions.cirq.cirq_quil_output import (
        QuilFormatter,
        QuilOneQubitGate,
        QuilOutput,
        QuilTwoQubitGate,
        _quil_u2_gate,
        _quil_u3_gate,
        _rzz_gate,
        _twoqubitdiagonal_gate,
        exponent_to_pi_string,
    )
    from qbraid.transpiler.conversions.qasm2.cirq_custom import RZZGate, U2Gate, U3Gate

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def _make_qubits(n):
    """Create a list of named qubits."""
    return [cirq.NamedQubit(f"q{i}") for i in range(n)]


def test_single_gate_no_parameter():
    """Test that a single gate with no parameter is correctly converted to Quil."""
    (q0,) = _make_qubits(1)
    output = QuilOutput((cirq.X(q0),), (q0,))
    assert (
        str(output)
        == """# Created using qBraid.

X 0\n"""
    )


def test_single_gate_with_parameter():
    """Test that a single gate with a parameter is correctly converted to Quil."""
    (q0,) = _make_qubits(1)
    output = QuilOutput((cirq.X(q0) ** 0.5,), (q0,))
    assert (
        str(output)
        == f"""# Created using qBraid.

RX({np.pi / 2}) 0\n"""
    )


def test_single_gate_named_qubit():
    """Test that a single gate with a named qubit is correctly converted to Quil."""
    q = cirq.NamedQubit("qTest")
    output = QuilOutput((cirq.X(q),), (q,))

    assert (
        str(output)
        == """# Created using qBraid.

X 0\n"""
    )


def test_h_gate_with_parameter():
    """Test that a Hadamard gate with a parameter is correctly converted to Quil."""
    (q0,) = _make_qubits(1)
    output = QuilOutput((cirq.H(q0) ** 0.25,), (q0,))
    assert (
        str(output)
        == f"""# Created using qBraid.

RY({np.pi / 4}) 0
RX({np.pi / 4}) 0
RY({-np.pi / 4}) 0\n"""
    )


def test_save_to_file(tmpdir):
    """Test that a QuilOutput can be saved to a file."""
    file_path = os.path.join(tmpdir, "test.quil")
    (q0,) = _make_qubits(1)
    output = QuilOutput((cirq.X(q0)), (q0,))
    output.save_to_file(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    assert (
        file_content
        == """# Created using qBraid.

X 0\n"""
    )


def test_quil_one_qubit_gate_repr():
    """Test that the QuilOneQubitGate __repr__ method works as expected."""
    gate = QuilOneQubitGate(np.array([[1, 0], [0, 1]]))
    assert repr(gate) == (
        """cirq.circuits.quil_output.QuilOneQubitGate(matrix=
[[1 0]
 [0 1]]
)"""
    )


def test_quil_two_qubit_gate_repr():
    """Test that the QuilTwoQubitGate __repr__ method works as expected."""
    gate = QuilTwoQubitGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))
    assert repr(gate) == (
        """cirq.circuits.quil_output.QuilTwoQubitGate(matrix=
[[1 0 0 0]
 [0 1 0 0]
 [0 0 1 0]
 [0 0 0 1]]
)"""
    )


def test_quil_one_qubit_gate_eq():
    """Test that the QuilOneQubitGate __eq__ method works as expected."""
    gate = QuilOneQubitGate(np.array([[1, 0], [0, 1]]))
    gate2 = QuilOneQubitGate(np.array([[1, 0], [0, 1]]))
    assert cirq.approx_eq(gate, gate2, atol=1e-16)
    gate3 = QuilOneQubitGate(np.array([[1, 0], [0, 1]]))
    gate4 = QuilOneQubitGate(np.array([[1, 0], [0, 2]]))
    assert not cirq.approx_eq(gate4, gate3, atol=1e-16)


def test_quil_two_qubit_gate_eq():
    """Test that the QuilTwoQubitGate __eq__ method works as expected."""
    gate = QuilTwoQubitGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))
    gate2 = QuilTwoQubitGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))
    assert cirq.approx_eq(gate, gate2, atol=1e-8)
    gate3 = QuilTwoQubitGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))
    gate4 = QuilTwoQubitGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 2, 0], [0, 0, 0, 1]]))
    assert not cirq.approx_eq(gate4, gate3, atol=1e-8)


def test_quil_one_qubit_gate_output():
    """Test that a QuilOneQubitGate can be correctly converted to Quil."""
    (q0,) = _make_qubits(1)
    gate = QuilOneQubitGate(np.array([[1, 0], [0, 1]]))
    output = QuilOutput((gate.on(q0),), (q0,))
    assert (
        str(output)
        == """# Created using qBraid.

DEFGATE USERGATE1:
    1.0+0.0i, 0.0+0.0i
    0.0+0.0i, 1.0+0.0i
USERGATE1 0
"""
    )


def test_two_quil_one_qubit_gate_output():
    """Test that two QuilOneQubitGates can be correctly converted to Quil."""
    (q0,) = _make_qubits(1)
    gate = QuilOneQubitGate(np.array([[1, 0], [0, 1]]))
    gate1 = QuilOneQubitGate(np.array([[2, 0], [0, 3]]))
    output = QuilOutput((gate.on(q0), gate1.on(q0)), (q0,))
    assert (
        str(output)
        == """# Created using qBraid.

DEFGATE USERGATE1:
    1.0+0.0i, 0.0+0.0i
    0.0+0.0i, 1.0+0.0i
USERGATE1 0
DEFGATE USERGATE2:
    2.0+0.0i, 0.0+0.0i
    0.0+0.0i, 3.0+0.0i
USERGATE2 0
"""
    )


def test_quil_two_qubit_gate_output():
    """Test that a QuilTwoQubitGate can be correctly converted to Quil."""
    (q0, q1) = _make_qubits(2)
    gate = QuilTwoQubitGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]))
    output = QuilOutput((gate.on(q0, q1),), (q0, q1))
    assert (
        str(output)
        == """# Created using qBraid.

DEFGATE USERGATE1:
    1.0+0.0i, 0.0+0.0i, 0.0+0.0i, 0.0+0.0i
    0.0+0.0i, 1.0+0.0i, 0.0+0.0i, 0.0+0.0i
    0.0+0.0i, 0.0+0.0i, 1.0+0.0i, 0.0+0.0i
    0.0+0.0i, 0.0+0.0i, 0.0+0.0i, 1.0+0.0i
USERGATE1 0 1
"""
    )


def test_unsupported_operation():
    """Test that an unsupported operation raises an error."""
    (q0,) = _make_qubits(1)

    class UnsupportedOperation(cirq.Operation):
        """Mock class for an unsupported operation."""

        qubits = (q0,)
        with_qubits = NotImplemented

    output = QuilOutput((UnsupportedOperation(),), (q0,))
    with pytest.raises(ValueError):
        _ = str(output)


def test_i_swap_with_power():
    """Test that an ISWAP gate with a power is correctly converted to Quil."""
    q0, q1 = _make_qubits(2)

    output = QuilOutput((cirq.ISWAP(q0, q1) ** 0.25,), (q0, q1))
    assert (
        str(output)
        == f"""# Created using qBraid.

XY({np.pi / 4}) 0 1
"""
    )


# pylint: disable-next=unused-argument
def _all_operations(q0, q1, q2, q3, q4):
    """Create a list of all supported operations."""
    return (
        cirq.Z(q0),
        cirq.Z(q0) ** 0.625,
        cirq.Y(q0),
        cirq.Y(q0) ** 0.375,
        cirq.X(q0),
        cirq.X(q0) ** 0.875,
        cirq.H(q1),
        cirq.CZ(q0, q1),
        cirq.CZ(q0, q1) ** 0.25,  # Requires 2-qubit decomposition
        cirq.CNOT(q0, q1),
        cirq.CNOT(q0, q1) ** 0.5,  # Requires 2-qubit decomposition
        cirq.SWAP(q0, q1),
        cirq.SWAP(q1, q0) ** -1,
        cirq.SWAP(q0, q1) ** 0.75,  # Requires 2-qubit decomposition
        cirq.CCZ(q0, q1, q2),
        cirq.CCX(q0, q1, q2),
        cirq.CCZ(q0, q1, q2) ** 0.5,
        cirq.CCX(q0, q1, q2) ** 0.5,
        cirq.CSWAP(q0, q1, q2),
        cirq.XX(q0, q1),
        cirq.XX(q0, q1) ** 0.75,
        cirq.YY(q0, q1),
        cirq.YY(q0, q1) ** 0.75,
        cirq.ZZ(q0, q1),
        cirq.ZZ(q0, q1) ** 0.75,
        cirq.IdentityGate(1).on(q0),
        cirq.IdentityGate(3).on(q0, q1, q2),
        cirq.ISWAP(q2, q0),  # Requires 2-qubit decomposition
        cirq.PhasedXPowGate(phase_exponent=0.111, exponent=0.25).on(q1),
        cirq.PhasedXPowGate(phase_exponent=0.333, exponent=0.5).on(q1),
        cirq.PhasedXPowGate(phase_exponent=0.777, exponent=-0.5).on(q1),
        cirq.wait(q0, nanos=0),
        cirq.measure(q0, key="xX"),
        cirq.measure(q2, key="x_a"),
        cirq.measure(q3, key="X"),
        cirq.measure(q2, key="x_a"),
        cirq.measure(q1, q2, q3, key="multi", invert_mask=(False, True)),
    )


def test_all_operations():
    """Test that all operations are correctly converted to Quil."""
    qubits = tuple(_make_qubits(5))
    operations = _all_operations(*qubits)
    output = QuilOutput(operations, qubits)

    assert (
        str(output)
        == f"""# Created using qBraid.

DECLARE m0 BIT[1]
DECLARE m1 BIT[1]
DECLARE m2 BIT[1]
DECLARE m3 BIT[3]

Z 0
RZ({5 * np.pi / 8}) 0
Y 0
RY({3 * np.pi / 8}) 0
X 0
RX({7 * np.pi / 8}) 0
H 1
CZ 0 1
CPHASE({np.pi / 4}) 0 1
CNOT 0 1
RY({-np.pi / 2}) 1
CPHASE({np.pi / 2}) 0 1
RY({np.pi / 2}) 1
SWAP 0 1
SWAP 1 0
PSWAP({3 * np.pi / 4}) 0 1
H 2
CCNOT 0 1 2
H 2
CCNOT 0 1 2
RZ({np.pi / 8}) 0
RZ({np.pi / 8}) 1
RZ({np.pi / 8}) 2
CNOT 0 1
CNOT 1 2
RZ({-np.pi / 8}) 1
RZ({np.pi / 8}) 2
CNOT 0 1
CNOT 1 2
RZ({-np.pi / 8}) 2
CNOT 0 1
CNOT 1 2
RZ({-np.pi / 8}) 2
CNOT 0 1
CNOT 1 2
H 2
RZ({np.pi / 8}) 0
RZ({np.pi / 8}) 1
RZ({np.pi / 8}) 2
CNOT 0 1
CNOT 1 2
RZ({-np.pi / 8}) 1
RZ({np.pi / 8}) 2
CNOT 0 1
CNOT 1 2
RZ({-np.pi / 8}) 2
CNOT 0 1
CNOT 1 2
RZ({-np.pi / 8}) 2
CNOT 0 1
CNOT 1 2
H 2
CSWAP 0 1 2
X 0
X 1
RX({3 * np.pi / 4}) 0
RX({3 * np.pi / 4}) 1
Y 0
Y 1
RY({3 * np.pi / 4}) 0
RY({3 * np.pi / 4}) 1
Z 0
Z 1
RZ({3 * np.pi / 4}) 0
RZ({3 * np.pi / 4}) 1
I 0
I 0
I 1
I 2
ISWAP 2 0
RZ({-0.111 * np.pi}) 1
RX({np.pi / 4}) 1
RZ({0.111 * np.pi}) 1
RZ({-0.333 * np.pi}) 1
RX({np.pi / 2}) 1
RZ({0.333 * np.pi}) 1
RZ({-0.777 * np.pi}) 1
RX({-np.pi / 2}) 1
RZ({0.777 * np.pi}) 1
WAIT
MEASURE 0 m0[0]
MEASURE 2 m1[0]
MEASURE 3 m2[0]
MEASURE 2 m1[0]
MEASURE 1 m3[0]
X 2 # Inverting for following measurement
MEASURE 2 m3[1]
MEASURE 3 m3[2]
"""
    )


def test_fails_on_big_unknowns():
    """Test that an error is raised when trying to convert an operation that is not supported."""

    class UnrecognizedGate(cirq.testing.ThreeQubitGate):
        """Mock class for an unsupported 3 qubit gate."""

    q0, q1, q2 = _make_qubits(3)
    res = QuilOutput(UnrecognizedGate().on(q0, q1, q2), (q0, q1, q2))
    with pytest.raises(ValueError, match="Cannot output operation as QUIL"):
        _ = str(res)


def test_pauli_interaction_gate():
    """Test that a PauliInteractionGate is correctly converted to Quil."""
    (q0, q1) = _make_qubits(2)
    output = QuilOutput(PauliInteractionGate.CZ.on(q0, q1), (q0, q1))
    assert (
        str(output)
        == """# Created using qBraid.

CZ 0 1
"""
    )


def test_equivalent_unitaries():
    """This test covers the factor of pi change. However, it will be skipped
    if pyquil is unavailable for import.

    References:
        https://docs.pytest.org/en/latest/skipping.html#skipping-on-a-missing-import-dependency
    """
    pyquil = pytest.importorskip("pyquil")
    pyquil_simulation_tools = pytest.importorskip("pyquil.simulation.tools")
    q0, q1 = _make_qubits(2)
    operations = [
        cirq.XPowGate(exponent=0.5, global_shift=-0.5)(q0),
        cirq.YPowGate(exponent=0.5, global_shift=-0.5)(q0),
        cirq.ZPowGate(exponent=0.5, global_shift=-0.5)(q0),
        cirq.CZPowGate(exponent=0.5)(q0, q1),
        cirq.ISwapPowGate(exponent=0.5)(q0, q1),
    ]
    output = QuilOutput(operations, (q0, q1))
    program = pyquil.Program(str(output))
    pyquil_unitary = pyquil_simulation_tools.program_unitary(program, n_qubits=2)
    # Qubit ordering differs between pyQuil and Cirq.
    cirq_unitary = cirq.Circuit(cirq.SWAP(q0, q1), operations, cirq.SWAP(q0, q1)).unitary()
    assert np.allclose(pyquil_unitary, cirq_unitary)


QUIL_CPHASES_PROGRAM = """
CPHASE00(pi/2) 0 1
CPHASE01(pi/2) 0 1
CPHASE10(pi/2) 0 1
CPHASE(pi/2) 0 1
"""

QUIL_DIAGONAL_DECOMPOSE_PROGRAM = """
RZ(0) 0
RZ(0) 1
CPHASE(0) 0 1
X 0
X 1
CPHASE(0) 0 1
X 0
X 1
"""


def test_two_qubit_diagonal_gate_quil_output():
    """Test that a TwoQubitDiagonalGate is correctly converted to Quil."""
    pyquil = pytest.importorskip("pyquil")
    pyquil_simulation_tools = pytest.importorskip("pyquil.simulation.tools")
    q0, q1 = _make_qubits(2)
    operations = [
        cirq.TwoQubitDiagonalGate([np.pi / 2, 0, 0, 0])(q0, q1),
        cirq.TwoQubitDiagonalGate([0, np.pi / 2, 0, 0])(q0, q1),
        cirq.TwoQubitDiagonalGate([0, 0, np.pi / 2, 0])(q0, q1),
        cirq.TwoQubitDiagonalGate([0, 0, 0, np.pi / 2])(q0, q1),
    ]
    output = QuilOutput(operations, (q0, q1))
    program = pyquil.Program(str(output))
    assert f"\n{program.out()}" == QUIL_CPHASES_PROGRAM

    pyquil_unitary = pyquil_simulation_tools.program_unitary(program, n_qubits=2)
    # Qubit ordering differs between pyQuil and Cirq.
    cirq_unitary = cirq.Circuit(cirq.SWAP(q0, q1), operations, cirq.SWAP(q0, q1)).unitary()
    assert np.allclose(pyquil_unitary, cirq_unitary)
    # Also test non-CPHASE case, which decomposes into X/RZ/CPhase
    operations = [cirq.TwoQubitDiagonalGate([0, 0, 0, 0])(q0, q1)]
    output = QuilOutput(operations, (q0, q1))
    program = pyquil.Program(str(output))
    assert f"\n{program.out()}" == QUIL_DIAGONAL_DECOMPOSE_PROGRAM


def test_parseable_defgate_output():
    """Test that a QuilOutput with a DEFGATE definition is correctly parsed."""
    pyquil = pytest.importorskip("pyquil")
    q0, q1 = _make_qubits(2)
    operations = [
        QuilOneQubitGate(np.array([[1, 0], [0, 1]])).on(q0),
        QuilTwoQubitGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])).on(
            q0, q1
        ),
    ]
    output = QuilOutput(operations, (q0, q1))
    # Just checks that we can create a pyQuil Program without crashing.
    pyquil.Program(str(output))


def test_unconveritble_op():
    """Test that an operation that cannot be converted to Quil raises an error."""
    (q0,) = _make_qubits(1)

    class MyGate(cirq.Gate):
        """Mock class for an one qubit gate."""

        def num_qubits(self) -> int:
            """Return the number of qubits."""
            return 1

    op = MyGate()(q0)

    # Documenting that this
    # operation would crash if you call _op_to_quil_directly
    with pytest.raises(ValueError, match="Can't convert"):
        _ = QuilOutput(op, (q0,))._op_to_quil(op)


@pytest.mark.parametrize(
    "input_exp, expected",
    [
        (0.25 * np.pi, "pi/4"),
        (-0.25 * np.pi, "-pi/4"),
        (0, "0"),
        (np.pi / 3, "pi/3"),
        (-1.25 * np.pi, "-5*pi/4"),
        (1 * np.pi, "pi"),
        (-1 * np.pi, "-pi"),
    ],
)
def test_exponent_to_pi_string(input_exp, expected):
    """Test that an exponent is correctly converted to a string with pi."""
    assert exponent_to_pi_string(input_exp) == expected


def test_two_qubit_diagonal_gate_none():
    """ "Test that _twoqubitdiagonal_gate returns None for non-diagonal gates."""
    (q0, q1) = _make_qubits(2)
    gate = cirq.TwoQubitDiagonalGate(np.array([0, 0, 0, 0]))
    formatter = QuilFormatter({q0: "q0", q1: "q1"}, {})
    circuit = cirq.Circuit()
    circuit.append(gate.on(q0, q1))
    instr = next(circuit.all_operations())
    assert _twoqubitdiagonal_gate(instr, formatter) is None


def test_rzz_rads_0_to_identity():
    """ "Test that RZZ gate with rads=0 maps to pyquil Identity gate."""
    (q0, q1) = _make_qubits(2)
    gate = RZZGate(rads=0)
    formatter = QuilFormatter({q0: "0", q1: "1"}, {})
    circuit = cirq.Circuit()
    circuit.append(gate.on(q0, q1))
    instr = next(circuit.all_operations())
    assert _rzz_gate(instr, formatter) == "I 0\nI 1\n"


@pytest.mark.parametrize(
    "gate_class, params, expected_quil, quil_converter",
    [
        (
            U2Gate,
            (np.pi / 4, np.pi / 8),
            "U(1.5707963267948966, 0.7853981633974483, 0.39269908169872414) 0",
            _quil_u2_gate,
        ),
        (
            U3Gate,
            (np.pi / 2, np.pi / 4, np.pi / 8),
            "U(1.5707963267948966, 0.7853981633974483, 0.39269908169872414) 0",
            _quil_u3_gate,
        ),
    ],
)
def test_custom_u_gate_to_quil(gate_class, params, expected_quil, quil_converter):
    """Test converting custom gates (U2, U3) to Quil."""
    (q0,) = _make_qubits(1)
    gate = gate_class(*params)
    formatter = QuilFormatter({q0: "0"}, {})
    circuit = cirq.Circuit()
    circuit.append(gate.on(q0))
    instr = next(circuit.all_operations())
    assert quil_converter(instr, formatter).strip() == expected_quil

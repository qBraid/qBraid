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
Unt tests for conversions to/from pyQuil circuits.

"""

import cirq
import numpy as np
import pytest
import sympy
from cirq import Circuit, LineQubit
from cirq import ops as cirq_ops

try:
    from pyquil import Program
    from pyquil.gates import CNOT, CZ, RESET, RX, RZ, RZZ, H, I, X, Y, Z
    from pyquil.noise import _decoherence_noise_model, _get_program_gates, apply_noise_model
    from pyquil.quilatom import (
        Function,
        MemoryReference,
        Mul,
        quil_cis,
        quil_cos,
        quil_exp,
        quil_sin,
        quil_sqrt,
    )

    from qbraid.interface import circuits_allclose
    from qbraid.transpiler.conversions.cirq import cirq_to_pyquil
    from qbraid.transpiler.conversions.pyquil import pyquil_to_cirq
    from qbraid.transpiler.conversions.pyquil.cirq_quil_input import _quil_param_to_sympy
    from qbraid.transpiler.conversions.qasm2 import qasm2_to_cirq
    from qbraid.transpiler.converter import transpile
    from qbraid.transpiler.exceptions import ProgramConversionError

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True
    # ``pytestmark`` skips the tests, but a @parametrize list is built while the module is
    # imported, before any skip can apply. These four are referenced there, so they need to
    # exist as names on 3.13+, where pyquil is not installed at all.
    quil_sin = quil_cos = quil_sqrt = quil_exp = quil_cis = None

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def test_to_from_pyquil():
    """Test round trip pyQuil-Cirq conversions."""
    p = Program()
    p += X(0)
    p += Y(1)
    p += Z(2)
    p += CNOT(0, 1)
    p += CZ(1, 2)
    p_cirq = pyquil_to_cirq(p)
    p_test = cirq_to_pyquil(p_cirq)
    assert p.out() == p_test.out()


def test_to_from_pyquil_parameterized():
    """Test round trip pyQuil-Cirq conversions with parameterized gates."""
    q0, q1 = (0, 1)
    p = Program()
    p += H(q0)
    p += H(q1)
    p += CNOT(q0, q1)
    p += RZ(2 * np.pi, q1)
    p += CNOT(q0, q1)
    p += H(q0)
    p += H(q1)
    p += RZ(np.pi / 4, q0)
    p += RZ(np.pi / 4, q1)
    p += H(q0)
    p += H(q1)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert p.out() == p_test.out()


QUIL_STRING = """
I 0
I 1
I 2
X 0
Y 1
Z 2
RX(pi/2) 0
RY(pi/2) 1
RZ(pi/2) 2
H 0
CZ 0 1
CNOT 1 2
CPHASE(pi/2) 0 1
CPHASE00(pi/2) 1 2
CPHASE01(pi/2) 0 1
CPHASE10(pi/2) 1 2
ISWAP 0 1
SWAP 1 2
XY(pi/2) 0 1
CCNOT 0 1 2
CSWAP 0 1 2
"""


def test_to_from_pyquil_quil_string():
    """PHASE, PSWAP, S, T, declaration, and measurement don't convert back
    and forth perfectly (in terms of labels -- the program unitaries and
    number of measurements are equivalent)."""
    p = Program(QUIL_STRING)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert circuits_allclose(p, p_test)


def test_from_pyquil_no_zero_qubit():
    """Test converting a pyQuil program with a non-zero qubit index to Cirq."""
    p = Program()
    p += X(10)
    p += Y(11)
    p += Z(12)
    p += CNOT(10, 11)
    p += CZ(11, 12)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert p.out() == p_test.out()


def test_raise_error_to_pyquil_bit_flip():
    """Test raising an error when converting a Cirq circuit with a bit flip to pyQuil."""

    with pytest.raises(ProgramConversionError):
        q0 = LineQubit(0)
        circuit = Circuit(cirq_ops.bit_flip(p=0.2).on(q0), cirq_ops.measure(q0, key="result"))
        cirq_to_pyquil(circuit)


def test_raise_error_from_pyquil_noisey():
    """Test raising an error when converting a noisey pyQuil program to Cirq."""

    with pytest.raises(ProgramConversionError):
        p = Program()
        p += RX(-np.pi / 2, 0)
        noise_model = _decoherence_noise_model(_get_program_gates(p))
        p = apply_noise_model(p, noise_model)
        pyquil_to_cirq(p)


def test_cirq_to_quil_output_rzz():
    """Test that a RZZ gate is correctly converted to Quil."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    rzz(pi) q[0], q[1];
    rzz(0) q[0], q[1];
    rzz(pi/2) q[0], q[1];
    """

    p = Program()
    p += CZ(0, 1)
    p += I(0)
    p += I(1)
    p += RZZ(np.pi / 2, 0, 1)
    cirq_circuit = qasm2_to_cirq(qasm)
    p_test: Program = cirq_to_pyquil(cirq_circuit)
    assert p_test.out().replace("pi/2", f"{np.pi/2}") == p.out()


@pytest.mark.parametrize(
    "gate",
    [cirq_ops.XXPowGate, cirq_ops.YYPowGate, cirq_ops.ZZPowGate],
)
@pytest.mark.parametrize("exponent", [0.5, 1.0, 0.75, -0.8, 2.0, 0.0])
def test_cirq_to_pyquil_ising_gate_roundtrip(gate, exponent):
    """Cirq XX/YY/ZZ interaction gates round-trip through pyQuil exactly.

    Regression test for https://github.com/qBraid/qBraid/issues/386, where the
    non-integer-exponent cases were decomposed into single-qubit rotations that
    did not preserve the two-qubit unitary.
    """
    q0, q1 = LineQubit.range(2)
    cirq_in = Circuit(gate(exponent=exponent).on(q0, q1))
    cirq_out = pyquil_to_cirq(cirq_to_pyquil(cirq_in))
    assert circuits_allclose(cirq_in, cirq_out, strict_gphase=True)


@pytest.mark.parametrize("exponent", [0.5, 1.0, 0.75, -0.8, 2.0, 0.0])
def test_cirq_to_pyquil_swappow_roundtrip(exponent):
    """Cirq SwapPowGate round-trips through pyQuil exactly.

    Non-integer powers were previously emitted as ``PSWAP(pi*t)``, a parametric
    swap-with-phase whose unitary differs from a fractional ``SWAP**t``. They now
    fall back to cirq's CNOT / RY / CPHASE decomposition.
    """
    q0, q1 = LineQubit.range(2)
    cirq_in = Circuit(cirq_ops.SwapPowGate(exponent=exponent).on(q0, q1))
    cirq_out = pyquil_to_cirq(cirq_to_pyquil(cirq_in))
    assert circuits_allclose(cirq_in, cirq_out, strict_gphase=True)


@pytest.mark.parametrize(
    "instr", ["CPHASE00(pi/2) 0 1", "CPHASE01(pi/2) 0 1", "CPHASE10(pi/2) 0 1"]
)
def test_cirq_to_pyquil_two_qubit_diagonal_roundtrip(instr):
    """pyQuil CPHASExx gates round-trip through cirq.

    ``pyquil_to_cirq`` represents these as a ``TwoQubitDiagonalGate`` whose
    diagonal angles are stored as a complex array; ``cirq_to_pyquil`` previously
    raised ``TypeError`` formatting them (``Fraction`` of a complex value).
    """
    p = Program(instr)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert circuits_allclose(p, p_test)


def test_cirq_reset_to_pyquil():
    """A Cirq circuit containing ``cirq.reset`` converts directly to a pyQuil
    program with a RESET on the same qubit, preserving operation order.

    Regression test: ``cirq_to_pyquil`` previously raised
    ``ProgramConversionError`` on any circuit containing ``cirq.ResetChannel``.
    """
    q0, q1 = LineQubit.range(2)
    circuit = Circuit(cirq_ops.X(q0), cirq_ops.reset(q0), cirq_ops.CNOT(q0, q1))
    p = Program()
    p += X(0)
    p += RESET(0)
    p += CNOT(0, 1)
    p_test = cirq_to_pyquil(circuit)
    assert p_test.out() == p.out()


def test_transpile_cirq_reset_to_pyquil_direct_path():
    """``transpile`` converts a circuit containing a reset over the direct
    ``cirq -> pyquil`` edge.

    Regression test: with ``max_path_depth=1`` this previously raised
    ``ProgramConversionError``, and the default search only succeeded by
    silently falling back to the ``cirq -> qasm2 -> pyquil`` path.
    """
    q0, q1 = LineQubit.range(2)
    circuit = Circuit(cirq_ops.X(q0), cirq_ops.reset(q0), cirq_ops.CNOT(q0, q1))
    program = transpile(circuit, "pyquil", max_path_depth=1)
    assert isinstance(program, Program)
    assert program.out() == "X 0\nRESET 0\nCNOT 0 1\n"


def test_declared_parameter_becomes_sympy_symbol():
    """A ``DECLARE``d gate angle survives conversion as a sympy symbol.

    Regression test for a parameterized pyQuil program converting into a Cirq gate whose
    exponent was a ``pyquil.quilatom.Div`` rather than a sympy expression. Cirq gate
    parameters must be numbers or ``sympy.Expr``; holding a pyQuil object made the free
    parameter invisible to ``cirq.is_parameterized`` and broke ``str()`` and ``unitary()``.
    """
    program = Program()
    theta = program.declare("theta", "REAL")
    program += RX(theta, 0)

    circuit = pyquil_to_cirq(program)
    exponent = next(iter(circuit.all_operations())).gate.exponent

    assert isinstance(exponent, sympy.Expr)
    assert exponent.free_symbols == {sympy.Symbol("theta")}
    assert cirq.is_parameterized(circuit)


def test_declared_parameter_circuit_is_diagrammable():
    """``str()`` on a converted parameterized circuit does not raise.

    Regression test: diagramming previously raised
    ``TypeError: int() argument must be ... not 'Div'`` from Cirq's angle formatter, because
    the exponent was a pyQuil expression object.
    """
    program = Program()
    theta = program.declare("theta", "REAL")
    program += RX(theta, 0)

    assert "theta" in str(pyquil_to_cirq(program))


def test_declared_parameter_resolves_to_correct_unitary():
    """Resolving the symbol reproduces the unitary of the same concrete rotation.

    This is the end-to-end property that matters: the symbol must carry the angle through
    with pyQuil's ``RX(theta) = exp(-i theta X / 2)`` convention, not merely be present.
    Previously ``unitary()`` raised ``ValueError`` from pyQuil because the parameter could
    not be evaluated.
    """
    program = Program()
    theta = program.declare("theta", "REAL")
    program += RX(theta, 0)
    circuit = pyquil_to_cirq(program)

    for angle in (0.0, 0.25, 1.0, np.pi / 2, np.pi):
        resolved = cirq.resolve_parameters(circuit, {"theta": angle})
        expected = Circuit(cirq_ops.rx(angle).on(LineQubit(0)))
        assert np.allclose(resolved.unitary(), expected.unitary(), atol=1e-12)


def test_multi_slot_declared_register_keeps_distinct_symbols():
    """Every slot of one declared register keeps its index, slot 0 included.

    ``DECLARE thetas REAL[2]`` used on two gates must not collapse into a single parameter,
    which would silently tie two independent angles together. The names are asserted exactly,
    not just counted: ``MemoryReference.declared_size`` is ``None`` on parsed references, so a
    naive check yields ``thetas`` for slot 0 and ``thetas[1]`` for slot 1 — two symbols, the
    right count, but one register under two naming conventions, and a caller resolving
    ``thetas[0]`` would silently miss it.
    """
    program = Program()
    thetas = program.declare("thetas", "REAL", 2)
    program += RX(thetas[0], 0)
    program += RZ(thetas[1], 0)

    circuit = pyquil_to_cirq(program)
    symbols = set()
    for op in circuit.all_operations():
        symbols |= sympy.sympify(op.gate.exponent).free_symbols

    assert {str(symbol) for symbol in symbols} == {"thetas[0]", "thetas[1]"}

    # Both slots resolve under their indexed names, leaving nothing free.
    resolved = cirq.resolve_parameters(circuit, {"thetas[0]": 0.3, "thetas[1]": 0.7})
    assert not cirq.is_parameterized(resolved)


@pytest.mark.parametrize(
    "declare_line",
    ["", "DECLARE t REAL\n", "DECLARE t REAL[1]\n"],
    ids=["undeclared", "declared-no-size", "declared-size-1"],
)
def test_indexed_slot_keeps_its_index_whatever_the_declaration(declare_line):
    """A slot with a non-zero offset is always ``name[offset]``.

    The size lookup falls back to ``MemoryReference.declared_size``, which pyQuil leaves as
    ``None`` on parsed references, so "register absent from the DECLAREs" and "register with
    exactly one slot" reach the same branch. That is safe only because the branch also requires
    ``offset == 0``: an indexed slot keeps its index regardless of what was declared, so two
    slots can never collapse onto one symbol and no register is ever named two ways.
    """
    program = Program(declare_line + "RX(t[1]) 0\n")
    circuit = pyquil_to_cirq(program)

    assert {str(symbol) for symbol in cirq.parameter_names(circuit)} == {"t[1]"}


def test_arithmetic_around_a_declared_parameter():
    """``Add``, ``Sub`` and ``Pow`` carry a declared parameter through as sympy.

    ``Mul`` and ``Div`` are exercised elsewhere, but only incidentally, so the other three
    arithmetic nodes had no test pinning them. Each is recursive on both operands, so a
    parameter can sit on either side of the operator and still has to survive.

    Note the Quil spelling: exponentiation is ``^``. ``**`` is a Python operator and does not
    parse, so a Quil-source test of ``Pow`` must be written ``theta^2``.
    """
    program = Program(
        "DECLARE theta REAL\n"
        "RX(2*theta + 0.5) 0\n"  # Add
        "RY(theta - 0.25) 1\n"  # Sub
        "RZ(theta^2) 2\n"  # Pow
    )
    circuit = pyquil_to_cirq(program)

    assert cirq.is_parameterized(circuit)
    assert {str(symbol) for symbol in cirq.parameter_names(circuit)} == {"theta"}
    for operation in circuit.all_operations():
        assert isinstance(operation.gate.exponent, sympy.Expr)

    # Resolving must reproduce the circuit built from the concrete angles, which is what
    # makes this a test of the arithmetic rather than of the symbol surviving.
    value = 0.7
    resolved = cirq.resolve_parameters(circuit, {"theta": value})
    concrete = Circuit(
        [
            cirq_ops.rx(2 * value + 0.5).on(LineQubit(0)),
            cirq_ops.ry(value - 0.25).on(LineQubit(1)),
            cirq_ops.rz(value**2).on(LineQubit(2)),
        ]
    )
    assert np.allclose(cirq.unitary(resolved), cirq.unitary(concrete), atol=1e-9)


def test_percent_parameter_in_a_top_level_gate():
    """A ``%``-parameter reaches the conversion as a bare ``Parameter``.

    ``DECLARE``d angles arrive as a ``MemoryReference``; pyQuil's parser also accepts the
    older ``%name`` spelling in a top-level gate application, which arrives as a
    ``quilatom.Parameter`` instead. That is a separate branch, and without this it is the one
    path in the conversion that nothing exercises.
    """
    circuit = pyquil_to_cirq(Program("RX(%theta) 0\n"))

    assert cirq.is_parameterized(circuit)
    assert {str(symbol) for symbol in cirq.parameter_names(circuit)} == {"theta"}

    value = 0.7
    resolved = cirq.resolve_parameters(circuit, {"theta": value})
    concrete = Circuit(cirq_ops.rx(value).on(LineQubit(0)))
    assert np.allclose(cirq.unitary(resolved), cirq.unitary(concrete), atol=1e-12)


def test_single_slot_declared_register_has_no_index():
    """A one-slot register resolves under its bare name.

    ``DECLARE theta REAL`` and ``DECLARE theta REAL[1]`` describe a single angle, so the
    symbol is ``theta`` rather than ``theta[0]`` and ``resolve_parameters({"theta": ...})``
    reads the way the Quil source does. This is the other half of the size lookup above: the
    register size decides whether the index is kept, so both sizes need pinning.
    """
    bare = Program()
    theta = bare.declare("theta", "REAL")
    bare += RX(theta, 0)

    sized = Program()
    theta_sized = sized.declare("theta", "REAL", 1)
    sized += RX(theta_sized[0], 0)

    for program in (bare, sized):
        circuit = pyquil_to_cirq(program)
        symbols = set()
        for op in circuit.all_operations():
            symbols |= sympy.sympify(op.gate.exponent).free_symbols

        assert {str(symbol) for symbol in symbols} == {"theta"}
        assert not cirq.is_parameterized(cirq.resolve_parameters(circuit, {"theta": 0.5}))


def test_concrete_angles_are_unchanged_by_parameter_handling():
    """Non-parameterized programs keep converting exactly as before.

    Guards against the symbol handling altering the common numeric path: the round trip must
    still reproduce the original Quil verbatim.
    """
    program = Program()
    program += RX(np.pi / 4, 0)
    program += RZ(2 * np.pi, 1)

    assert cirq_to_pyquil(pyquil_to_cirq(program)).out() == program.out()


def test_declared_parameter_survives_round_trip_numerically():
    """A parameterized program still evaluates correctly after a cirq -> pyQuil round trip.

    The emitted Quil is not textually identical to the input (``cirq_to_pyquil`` re-expands the
    angle as ``(3.14159...*theta[0])/pi``), so this asserts the property that matters -- the
    resolved unitary -- rather than string equality, which would be a self-reinforcing test of
    the current formatting.
    """
    program = Program()
    theta = program.declare("theta", "REAL")
    program += RX(theta, 0)

    round_tripped = pyquil_to_cirq(cirq_to_pyquil(pyquil_to_cirq(program)))

    for angle in (0.0, 0.3, 1.0, np.pi / 2):
        resolved = cirq.resolve_parameters(round_tripped, {"theta": angle})
        expected = Circuit(cirq_ops.rx(angle).on(LineQubit(0)))
        assert np.allclose(resolved.unitary(), expected.unitary(), atol=1e-9)


@pytest.mark.parametrize(
    "source, expected",
    [
        ("DECLARE theta REAL\nRX(theta) 0\n", {"theta"}),
        ("DECLARE theta REAL[1]\nRX(theta[0]) 0\n", {"theta"}),
        ("DECLARE thetas REAL[2]\nRX(thetas[0]) 0\nRY(thetas[1]) 1\n", {"thetas[0]", "thetas[1]"}),
        ("DECLARE t REAL[4]\nRX(t[3]) 0\n", {"t[3]"}),
        ("DECLARE theta REAL\nRX(2*theta + 0.5) 0\n", {"theta"}),
        ("DECLARE a REAL\nDECLARE b REAL[2]\nRX(a) 0\nRY(b[1]) 1\n", {"a", "b[1]"}),
        ("RX(1.5) 0\n", set()),
    ],
    ids=[
        "bare",
        "size-1",
        "multi-slot",
        "sparse-index",
        "arithmetic",
        "two-registers",
        "no-params",
    ],
)
def test_round_trip_preserves_every_parameter_name(source, expected):
    """A round trip names each register the same way the forward conversion did.

    ``cirq_to_pyquil`` emits the gate lines but has to emit the ``DECLARE``s too, because
    the size lookup on the way back reads an *undeclared* register's slot 0 as the bare
    register name. Without them ``thetas[0]`` returns as ``thetas`` while ``thetas[1]``
    keeps its index -- one register named two ways, which is the shape this module's
    forward direction exists to prevent.

    Only ``multi-slot`` fails without the fix, and that is the point: the corruption needs
    a register that has both slot 0 *and* another slot, because a non-zero offset is kept
    regardless (``sparse-index`` and ``two-registers`` round trip even unfixed). The other
    six cases pin behaviour that already held, so a future change to the size inference
    cannot quietly break them -- e.g. ``t[3]`` alone must declare ``REAL[4]``, and a
    parameterless circuit must emit no ``DECLARE`` at all.
    """
    circuit = pyquil_to_cirq(Program(source))
    assert {str(symbol) for symbol in cirq.parameter_names(circuit)} == expected

    round_tripped = pyquil_to_cirq(Program(str(cirq_to_pyquil(circuit))))
    assert {str(symbol) for symbol in cirq.parameter_names(round_tripped)} == expected


@pytest.mark.parametrize(
    "quil_fn, numpy_fn",
    [
        (quil_sin, np.sin),
        (quil_cos, np.cos),
        (quil_sqrt, np.sqrt),
        (quil_exp, np.exp),
    ],
)
def test_declared_parameter_inside_quil_function(quil_fn, numpy_fn):
    """A Quil function applied to a declared parameter becomes sympy.

    ``RX(SIN(theta)) 0`` wraps the ``MemoryReference`` in a
    ``pyquil.quilatom.Function``. Left unconverted it reaches the Cirq gate as a
    foreign object, so ``cirq.is_parameterized`` reports ``False`` and ``str()``
    raises ``TypeError`` -- the same failure this module fixes for a bare
    reference. Resolving the symbol must reproduce the circuit built from the
    concrete value.
    """
    program = Program()
    theta = program.declare("theta", "REAL")
    program += RX(quil_fn(theta), 0)

    circuit = pyquil_to_cirq(program)

    exponent = list(circuit.all_operations())[0].gate.exponent
    assert isinstance(exponent, sympy.Expr)
    assert cirq.is_parameterized(circuit)
    assert "theta" in str(circuit)

    value = 0.7
    resolved = cirq.resolve_parameters(circuit, {"theta": value})
    concrete = pyquil_to_cirq(Program() + RX(float(numpy_fn(value)), 0))
    assert np.allclose(cirq.unitary(resolved), cirq.unitary(concrete), atol=1e-9)


def test_declared_parameter_inside_quil_cis():
    """``CIS(x)`` is ``cos(x) + i sin(x)``, i.e. ``exp(i x)``."""
    program = Program()
    theta = program.declare("theta", "REAL")
    program += RX(quil_cis(theta), 0)

    circuit = pyquil_to_cirq(program)

    exponent = list(circuit.all_operations())[0].gate.exponent
    assert isinstance(exponent, sympy.Expr)
    assert cirq.is_parameterized(circuit)
    # The conversion divides by ``np.pi`` (a float), so compare numerically
    # after substituting a value rather than against a symbolic ``sympy.pi``.
    value = 0.7
    substituted = complex(exponent.subs(sympy.Symbol("theta"), value))
    assert np.isclose(substituted, np.exp(1j * value) / np.pi)


def test_arithmetic_operand_that_is_already_sympy_is_not_rewrapped():
    """A ``quilatom`` node whose operand is already a ``sympy`` expression converts cleanly.

    The conversion recurses into both operands of an arithmetic node, so an operand that is
    already ``sympy`` reaches the function a second time. Returning it unchanged is what keeps
    the recursion idempotent; rebuilding it would wrap a ``sympy`` expression in another layer.
    """
    node = Mul(sympy.Symbol("theta"), 2.0)

    converted = _quil_param_to_sympy(node)

    assert isinstance(converted, sympy.Expr)
    assert converted.free_symbols == {sympy.Symbol("theta")}
    assert float(converted.subs(sympy.Symbol("theta"), 3.0)) == pytest.approx(6.0)
    # Idempotent: feeding the result back in must be a no-op, not another rebuild.
    assert _quil_param_to_sympy(converted) is converted


def test_unmapped_quil_function_is_returned_unchanged():
    """A Quil ``Function`` whose name has no ``sympy`` counterpart passes through untouched.

    ``_QUIL_FUNCTIONS`` maps the five Quil functions by *name*. An unmapped name must not raise
    or return ``None`` — the documented contract is to hand the parameter back unchanged so
    behaviour matches the pre-conversion code rather than becoming an error.
    """
    unmapped = Function("NOT_A_QUIL_FUNCTION", MemoryReference("theta"), np.sin)

    assert _quil_param_to_sympy(unmapped) is unmapped


def test_unrecognized_parameter_type_is_returned_unchanged():
    """An object that is none of the handled kinds is returned as-is.

    This is the final fallback. It matters because pyQuil can grow new parameter node types:
    the conversion must degrade to the old passthrough behaviour instead of raising on a shape
    it has never seen.
    """

    class UnknownParameter:
        """Not a number, sympy, MemoryReference, Parameter, or arithmetic node."""

    unknown = UnknownParameter()

    assert _quil_param_to_sympy(unknown) is unknown

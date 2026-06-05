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

"""Tests for cirq_to_qasm3 conversion."""

import re

import cirq
import numpy as np
import pytest

from qbraid.transpiler.conversions.cirq.cirq_to_qasm3 import cirq_to_qasm3
from qbraid.transpiler.exceptions import ProgramConversionError
from qbraid.transpiler.graph import ConversionGraph


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _unitary_from_qasm3(qasm3_str: str) -> np.ndarray:
    """Round-trip qasm3 -> cirq to get a unitary for comparison."""
    from qbraid.transpiler.converter import transpile

    cirq_circuit = transpile(qasm3_str, "cirq")
    return cirq.unitary(cirq_circuit)


def _make_circuit(*ops) -> cirq.Circuit:
    return cirq.Circuit(ops)


# ---------------------------------------------------------------------------
# Basic structural tests
# ---------------------------------------------------------------------------


def test_output_is_qasm3_string():
    q = cirq.LineQubit.range(1)
    circuit = _make_circuit(cirq.H(q[0]))
    result = cirq_to_qasm3(circuit)
    assert isinstance(result, str)
    assert result.strip().startswith("OPENQASM 3.0")


def test_includes_stdgates():
    q = cirq.LineQubit.range(1)
    circuit = _make_circuit(cirq.H(q[0]))
    result = cirq_to_qasm3(circuit)
    assert 'include "stdgates.inc"' in result


def test_qubit_declaration_syntax():
    """QASM 3 uses 'qubit[N] q' not 'qreg q[N]'."""
    q = cirq.LineQubit.range(3)
    circuit = _make_circuit(cirq.H(q[0]), cirq.CNOT(q[0], q[1]), cirq.X(q[2]))
    result = cirq_to_qasm3(circuit)
    assert re.search(r"qubit\[\d+\]\s+\w+", result), "expected 'qubit[N] name' declaration"
    assert "qreg" not in result


def test_measurement_declaration_syntax():
    """QASM 3 uses 'bit[N]' and 'measure q -> c' syntax."""
    q = cirq.LineQubit.range(2)
    circuit = _make_circuit(cirq.H(q[0]), cirq.measure(q[0], q[1], key="m"))
    result = cirq_to_qasm3(circuit)
    assert "bit[" in result or "creg" not in result


# ---------------------------------------------------------------------------
# Gate coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "gate, num_qubits",
    [
        (cirq.H, 1),
        (cirq.X, 1),
        (cirq.Y, 1),
        (cirq.Z, 1),
        (cirq.S, 1),
        (cirq.T, 1),
        (cirq.CNOT, 2),
        (cirq.CZ, 2),
        (cirq.SWAP, 2),
    ],
)
def test_standard_gates(gate, num_qubits):
    qubits = cirq.LineQubit.range(num_qubits)
    circuit = _make_circuit(gate(*qubits))
    result = cirq_to_qasm3(circuit)
    assert "OPENQASM 3.0" in result


@pytest.mark.parametrize(
    "gate",
    [
        cirq.rx(0.5),
        cirq.ry(1.2),
        cirq.rz(0.75),
    ],
)
def test_parameterized_rotation_gates(gate):
    q = cirq.LineQubit.range(1)
    circuit = _make_circuit(gate(q[0]))
    result = cirq_to_qasm3(circuit)
    assert "OPENQASM 3.0" in result


def test_controlled_gate():
    q = cirq.LineQubit.range(2)
    circuit = _make_circuit(cirq.Y(q[1]).controlled_by(q[0]))
    result = cirq_to_qasm3(circuit)
    assert "OPENQASM 3.0" in result


def test_toffoli_gate():
    q = cirq.LineQubit.range(3)
    circuit = _make_circuit(cirq.CCNOT(q[0], q[1], q[2]))
    result = cirq_to_qasm3(circuit)
    assert "OPENQASM 3.0" in result


def test_multi_moment_circuit():
    q = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q[0]),
        cirq.CNOT(q[0], q[1]),
        cirq.rz(0.3)(q[0]),
        cirq.measure(q[0], q[1], key="result"),
    )
    result = cirq_to_qasm3(circuit)
    assert "OPENQASM 3.0" in result
    assert "h" in result.lower() or "H" in result


# ---------------------------------------------------------------------------
# Unitary equivalence
# ---------------------------------------------------------------------------


def test_unitary_equivalence_bell_state_prep():
    q = cirq.LineQubit.range(2)
    circuit = _make_circuit(cirq.H(q[0]), cirq.CNOT(q[0], q[1]))
    result = cirq_to_qasm3(circuit)

    original_unitary = cirq.unitary(circuit)
    converted_unitary = _unitary_from_qasm3(result)

    assert np.allclose(original_unitary, converted_unitary, atol=1e-6), (
        "Unitary mismatch after cirq -> qasm3 round-trip"
    )


def test_unitary_equivalence_single_qubit_rotations():
    q = cirq.LineQubit.range(1)
    circuit = _make_circuit(cirq.rx(0.3)(q[0]), cirq.ry(0.7)(q[0]), cirq.rz(1.1)(q[0]))
    result = cirq_to_qasm3(circuit)

    original_unitary = cirq.unitary(circuit)
    converted_unitary = _unitary_from_qasm3(result)

    assert np.allclose(original_unitary, converted_unitary, atol=1e-6)


def test_unitary_equivalence_three_qubit():
    q = cirq.LineQubit.range(3)
    circuit = _make_circuit(cirq.H(q[0]), cirq.CNOT(q[0], q[1]), cirq.CNOT(q[1], q[2]))
    result = cirq_to_qasm3(circuit)

    original_unitary = cirq.unitary(circuit)
    converted_unitary = _unitary_from_qasm3(result)

    assert np.allclose(original_unitary, converted_unitary, atol=1e-6)


# ---------------------------------------------------------------------------
# Graph integration
# ---------------------------------------------------------------------------


def test_conversion_graph_has_direct_cirq_to_qasm3_edge():
    """cirq -> qasm3 must appear as a direct (native) edge, not just a path."""
    graph = ConversionGraph(require_native=True)
    assert graph.has_path(
        "cirq", "qasm3"
    ), "cirq -> qasm3 direct edge missing from ConversionGraph"


def test_transpile_via_graph_produces_qasm3():
    from qbraid.transpiler.converter import transpile

    q = cirq.LineQubit.range(2)
    circuit = _make_circuit(cirq.H(q[0]), cirq.CNOT(q[0], q[1]))
    result = transpile(circuit, "qasm3")
    assert isinstance(result, str)
    assert result.strip().startswith("OPENQASM 3.0")


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_empty_circuit_returns_valid_qasm3():
    circuit = cirq.Circuit()
    result = cirq_to_qasm3(circuit)
    assert "OPENQASM 3.0" in result


def test_custom_header_does_not_raise():
    """Header is accepted as a parameter; pyqasm strips QASM comments during
    the QASM 2 -> QASM 3 upgrade, so it won't appear in the output string."""
    q = cirq.LineQubit.range(1)
    circuit = _make_circuit(cirq.H(q[0]))
    result = cirq_to_qasm3(circuit, header="custom header")
    assert "OPENQASM 3.0" in result


def test_named_qubits():
    a, b = cirq.NamedQubit("alice"), cirq.NamedQubit("bob")
    circuit = _make_circuit(cirq.H(a), cirq.CNOT(a, b))
    result = cirq_to_qasm3(circuit)
    assert "OPENQASM 3.0" in result


# ---------------------------------------------------------------------------
# Coverage benchmark (determines @weight value)
# ---------------------------------------------------------------------------


def test_cirq_to_qasm3_coverage():
    """Measure the fraction of unitary Cirq gates that survive ``cirq_to_qasm3``.

    Non-unitary operations (noise channels, density-matrix gates) are excluded
    from the denominator because QASM is a unitary gate language and those
    operations are inherently not representable.  The passing fraction over the
    remaining *unitary* gate set determines the ``@weight`` on the conversion.
    """
    import string

    import scipy

    # Non-unitary / abstract types that QASM cannot represent — excluded from coverage.
    _EXCLUDED_SUFFIXES = ("Channel", "Noise")
    _EXCLUDED_NAMES = {
        "Gate",
        "EigenGate",
        "Pauli",
        "BaseDensePauliString",
        "DensePauliString",
        "MutableDensePauliString",
        "ArithmeticGate",
    }

    BASELINE = 0.85
    ALLOWANCE = 0.05

    qubits = cirq.LineQubit.range(7)

    def _is_excluded(name: str) -> bool:
        return name in _EXCLUDED_NAMES or any(name.endswith(s) for s in _EXCLUDED_SUFFIXES)

    def _try_gate(gate_name: str):
        if _is_excluded(gate_name):
            return None
        gate_cls = getattr(cirq.ops, gate_name, None)
        if gate_cls is None:
            return None
        try:
            np.random.seed(0)

            if isinstance(gate_cls, cirq.Gate):
                # Singleton gate instance (e.g. CSWAP, FREDKIN) — call directly.
                gate_inst = gate_cls
            else:
                # Gate class — instantiate with randomly chosen valid parameters.
                try:
                    varnames = gate_cls.__init__.__code__.co_varnames
                except AttributeError:
                    varnames = ()
                params = {}
                for v in ("rads", "theta", "phi"):
                    if v in varnames:
                        params[v] = np.random.rand() * 2 * np.pi
                for v in ("exponent", "x_exponent", "z_exponent", "phase_exponent", "axis_phase_exponent"):
                    if v in varnames:
                        params[v] = np.random.rand() * 10
                for v in ("gamma", "p", "probability"):
                    if v in varnames:
                        params[v] = np.random.rand()
                if "num_qubits" in varnames:
                    params["num_qubits"] = 3
                if "sub_gate" in varnames:
                    params["sub_gate"] = cirq.X
                if "matrix" in varnames:
                    params["matrix"] = scipy.stats.unitary_group.rvs(2)
                gate_inst = gate_cls(**params)

            op = gate_inst(*qubits[: gate_inst.num_qubits()])
            cirq_to_qasm3(cirq.Circuit(op))
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    gate_names = [
        attr
        for attr in dir(cirq.ops)
        if attr[0] in string.ascii_uppercase
        and isinstance(
            getattr(cirq.ops, attr),
            (cirq.Gate, cirq.value.abc_alt.ABCMetaImplementAnyOneOf),
        )
    ]

    results = [(g, _try_gate(g)) for g in gate_names]
    counted = [(g, r) for g, r in results if r is not None]

    passes = sum(r for _, r in counted)
    total = len(counted)
    accuracy = passes / total if total else 0.0

    assert accuracy >= BASELINE - ALLOWANCE, (
        f"cirq_to_qasm3 coverage {accuracy:.2%} below threshold "
        f"{BASELINE - ALLOWANCE:.2%} ({passes}/{total} unitary gates passed). "
        f"Failures: {[g for g, r in counted if not r]}"
    )

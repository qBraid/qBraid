# Copyright 2026 qBraid
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
Unit tests for the ``qiskit -> aqt`` transpiler edge, the ported qiskit angle-wrapping passes and
serializer, the ``aqt`` program-type registration, and the ``AQTProgram`` wrapper.

The AQT native circuit is produced entirely by the ``qiskit -> aqt`` transpiler edge (no device
serialize hook, no ``qiskit-aqt-provider`` dependency). ``aqt-connector`` is a real installed
dependency here; no network access occurs.
"""

from __future__ import annotations

import math

import pytest
from aqt_connector.models.circuits import QuantumCircuit
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit

from qbraid.programs import QPROGRAM_ALIASES, QPROGRAM_REGISTRY, get_program_type_alias
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.aqt import AQTProgram
from qbraid.transpiler import ConversionGraph, transpile
from qbraid.transpiler.conversions.qiskit.qiskit_to_aqt import (
    WrapRxxAngles,
    _qiskit_to_aqt_circuit,
    rewrite_rx_as_r,
    wrap_rxx_angle,
)

# ---------------------------------------------------------------------------
# transpiler edge
# ---------------------------------------------------------------------------


def test_conversion_graph_has_qiskit_to_aqt_edge():
    """The ``qiskit -> aqt`` edge is registered in the conversion graph."""
    assert ConversionGraph().has_edge("qiskit", "aqt") is True


def test_transpile_qiskit_to_aqt_returns_native_circuit():
    """``transpile(qiskit_circuit, "aqt")`` returns a native ``aqt_connector`` circuit."""
    qc = QiskitCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    out = transpile(qc, "aqt")
    assert type(out).__module__ == "aqt_connector.models.circuits"
    assert type(out).__name__ == "QuantumCircuit"
    assert out.number_of_qubits == 2
    assert out.repetitions == 1
    assert get_program_type_alias(out) == "aqt"


def test_transpile_ghz_produces_valid_circuit_with_measurement_last():
    """A GHZ transpile decomposes to the AQT native basis and validates; measurement is last."""
    ghz = QiskitCircuit(3)
    ghz.h(0)
    ghz.cx(0, 1)
    ghz.cx(1, 2)
    ghz.measure_all()

    out = transpile(ghz, "aqt")
    assert out.number_of_qubits == 3

    ops = out.quantum_circuit.root
    op_names = {type(op.root).__name__ for op in ops}
    assert op_names <= {"GateRZ", "GateR", "GateRXX", "Measure"}
    assert type(ops[-1].root).__name__ == "Measure"

    # The produced native circuit re-validates against the aqt_connector model.
    QuantumCircuit.model_validate(out.model_dump())


def test_transpile_non_adjacent_cx_wraps_angles_into_api_ranges():
    """A non-adjacent CX (+ negative rx) exercises the angle-wrapping passes; angles stay in range.

    Angles are emitted in units of pi: ``R.theta in [0, 1]`` and ``RXX.theta in [0, 0.5]``.
    """
    qc = QiskitCircuit(3)
    qc.h(0)
    qc.cx(0, 2)  # non-adjacent -> routed + angle-wrapped
    qc.rx(-1.7, 1)  # negative angle -> exercises RewriteRxAsR
    qc.measure_all()

    out = transpile(qc, "aqt")
    assert out.number_of_qubits == 3

    ops = out.quantum_circuit.root
    assert type(ops[-1].root).__name__ == "Measure"
    for op in ops:
        gate = op.root
        if type(gate).__name__ == "GateR":
            assert 0 <= gate.theta <= 1
        if type(gate).__name__ == "GateRXX":
            assert 0 <= gate.theta <= 0.5

    QuantumCircuit.model_validate(out.model_dump())


# ---------------------------------------------------------------------------
# ported qiskit passes
# ---------------------------------------------------------------------------


def test_rewrite_rx_as_r_positive_angle():
    """``Rx(theta)`` with theta >= 0 becomes ``R(theta, phi=0)``."""
    instruction = rewrite_rx_as_r(0.5)
    theta, phi = (float(p) for p in instruction.params)
    assert theta == pytest.approx(0.5)
    assert phi == pytest.approx(0.0)


def test_rewrite_rx_as_r_negative_angle():
    """A negative ``Rx`` angle is folded to a positive theta with ``phi = pi``."""
    instruction = rewrite_rx_as_r(-0.5)
    theta, phi = (float(p) for p in instruction.params)
    assert theta == pytest.approx(0.5)
    assert phi == pytest.approx(math.pi)


@pytest.mark.parametrize(
    "theta",
    [
        0.3,  # fast path |theta| <= pi/2
        -0.3,  # fast path, negative -> RZ-sandwiched RXX
        math.pi,  # |theta| in (pi/2, 3pi/2] branch
        -math.pi,  # same branch, negative sign
        1.9 * math.pi,  # |theta| > 3pi/2 branch after mod
        -1.9 * math.pi,  # same branch, negative sign
    ],
)
def test_wrap_rxx_angle_covers_all_branches(theta):
    """``wrap_rxx_angle`` returns a composite ``Rxx-wrapped`` instruction for every angle regime."""
    instruction = wrap_rxx_angle(theta)
    assert instruction.name.startswith("Rxx-wrapped")


def test_wrap_rxx_angles_pass_substitutes_out_of_range_gate():
    """The ``WrapRxxAngles`` pass substitutes an out-of-range ``rxx`` with a wrapped composite."""
    qc = QiskitCircuit(2)
    qc.rxx(3.0, 0, 1)  # 3.0 > pi/2 -> out of range, triggers substitution

    out = dag_to_circuit(WrapRxxAngles().run(circuit_to_dag(qc)))
    op_names = [instruction.operation.name for instruction in out.data]
    assert any(name.startswith("Rxx-wrapped") for name in op_names)


def test_wrap_rxx_angles_pass_leaves_in_range_gate_untouched():
    """An ``rxx`` already in ``[0, pi/2]`` is left unchanged by the pass."""
    qc = QiskitCircuit(2)
    qc.rxx(0.3, 0, 1)  # in range -> untouched

    out = dag_to_circuit(WrapRxxAngles().run(circuit_to_dag(qc)))
    op_names = [instruction.operation.name for instruction in out.data]
    assert op_names == ["rxx"]


def test_qiskit_to_aqt_circuit_requires_measurement():
    """A circuit without a measurement is rejected."""
    qc = QiskitCircuit(1)
    qc.rz(0.5, 0)
    with pytest.raises(ValueError, match="at least one measurement"):
        _qiskit_to_aqt_circuit(qc)


def test_qiskit_to_aqt_circuit_rejects_non_basis_gate():
    """A gate outside ``{rz, r, rxx}`` (plus measure/barrier) is rejected."""
    qc = QiskitCircuit(1)
    qc.x(0)
    qc.measure_all()
    with pytest.raises(ValueError, match="not in basis gate set"):
        _qiskit_to_aqt_circuit(qc)


def test_qiskit_to_aqt_circuit_rejects_mid_circuit_measurement():
    """A gate after a measurement is rejected (measurements must be terminal)."""
    qc = QiskitCircuit(1, 1)
    qc.rz(0.5, 0)
    qc.measure(0, 0)
    qc.rz(0.5, 0)
    with pytest.raises(ValueError, match="end of the circuit"):
        _qiskit_to_aqt_circuit(qc)


# ---------------------------------------------------------------------------
# program-type registration
# ---------------------------------------------------------------------------


def test_aqt_alias_registered_to_native_type():
    """The aqt_connector native circuit is registered under the ``aqt`` transpiler alias."""
    assert "aqt" in QPROGRAM_ALIASES
    assert QPROGRAM_REGISTRY["aqt"] is QuantumCircuit


def test_get_program_type_alias_for_native_circuit(aqt_circuit):
    """A native ``aqt_connector`` circuit resolves to the ``aqt`` alias."""
    assert get_program_type_alias(aqt_circuit()) == "aqt"


@pytest.mark.parametrize("value", [{}, "not-a-circuit", 42, [1, 2, 3]])
def test_non_aqt_values_do_not_resolve_to_aqt(value):
    """Dicts, strings, ints, and lists do not resolve to the ``aqt`` alias."""
    assert get_program_type_alias(value, safe=True) != "aqt"


def test_qiskit_circuit_does_not_resolve_to_aqt():
    """A qiskit circuit resolves to ``qiskit``, not ``aqt``."""
    assert get_program_type_alias(QiskitCircuit(1)) == "qiskit"


# ---------------------------------------------------------------------------
# AQTProgram
# ---------------------------------------------------------------------------


def test_aqt_program_qubit_and_bit_counts(aqt_circuit):
    """``AQTProgram`` exposes qubits/num_qubits from the wrapped circuit and zero classical bits."""
    program = AQTProgram(aqt_circuit(number_of_qubits=3))
    assert program.qubits == [0, 1, 2]
    assert program.num_qubits == 3
    assert program.num_clbits == 0


def test_aqt_program_serialize_not_implemented(aqt_circuit):
    """Like ``QiskitCircuit``, ``AQTProgram`` does not implement ``serialize``."""
    program = AQTProgram(aqt_circuit())
    with pytest.raises(NotImplementedError):
        program.serialize()


@pytest.mark.parametrize("bad", [{"a": 1}, "circuit", 3.14])
def test_aqt_program_wrong_type_raises(bad):
    """Constructing ``AQTProgram`` with a non-AQT program raises ``ProgramTypeError``."""
    with pytest.raises(ProgramTypeError):
        AQTProgram(bad)

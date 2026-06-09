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
Tests for qBraid transpiler conversion extras.

"""

import importlib.util
from typing import Callable

import braket.circuits
import pytest

try:
    import pyqir

    pyqir_installed = True
except ImportError:
    pyqir_installed = False


from qbraid.interface import assert_allclose_up_to_global_phase
from qbraid.passes.qasm.compat import normalize_qasm_gate_params
from qbraid.programs import load_program
from qbraid.transpiler.conversions.pennylane import(
    pennylane_to_braket,
    pennylane_to_cirq,
    pennylane_to_qiskit,
)
from qbraid.transpiler.conversions.pytket import pytket_to_pyqir
from qbraid.transpiler.conversions.qasm3 import autoqasm_to_qasm3
from qbraid.transpiler.conversions.qiskit import (
    qiskit_to_braket,
    qiskit_to_pennylane,
    qiskit_to_pyqir,
)
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.graph import ConversionGraph


def has_extra(conversion_func: Callable) -> bool:
    """
    Check if the conversion function requires extra packages.

    Args:
        conversion_func (Callable): The conversion function to check for extra requirements.

    Returns:
        bool: True if all required extra packages are importable, False otherwise.
    """
    extras = getattr(conversion_func, "requires_extras", [])
    return all(importlib.util.find_spec(module_name) is not None for module_name in extras)


@pytest.mark.skipif(not has_extra(qiskit_to_braket), reason="Extra not installed")
@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_qiskit_to_braket_extra(bell_circuit):
    """Test qiskit-braket-provider transpiler conversion extra."""
    qiskit_circuit, _ = bell_circuit
    conversions = [Conversion("qiskit", "braket", qiskit_to_braket)]
    graph = ConversionGraph(conversions)
    program = transpile(qiskit_circuit, "braket", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, braket.circuits.Circuit)


@pytest.mark.skipif(not has_extra(qiskit_to_pyqir), reason="Extra not installed")
@pytest.mark.skipif(not pyqir_installed, reason="pyqir not installed")
@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_qiskit_to_pyqir_extra(bell_circuit):
    """Test qiskit-qir transpiler conversion extra."""
    qiskit_circuit, _ = bell_circuit
    conversions = [Conversion("qiskit", "pyqir", qiskit_to_pyqir)]
    graph = ConversionGraph(conversions)
    program = transpile(qiskit_circuit, "pyqir", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, pyqir.Module)


@pytest.mark.skipif(not has_extra(pytket_to_pyqir), reason="Extra not installed")
@pytest.mark.skipif(not pyqir_installed, reason="pyqir not installed")
def test_pytket_to_pyqir_extra():
    """Test pytket-qir transpiler conversion extra."""
    # pylint: disable-next=import-outside-toplevel
    from pytket.circuit import Circuit

    pytket_circuit = Circuit(2)
    pytket_circuit.H(0)
    pytket_circuit.CX(0, 1)
    pytket_circuit.measure_all()

    conversions = [Conversion("pytket", "pyqir", pytket_to_pyqir)]
    graph = ConversionGraph(conversions)
    program = transpile(pytket_circuit, "pyqir", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, pyqir.Module)

    # the module is valid QIR and actually encodes the H -> CX -> measure circuit
    assert program.verify() is None
    ir = str(program)
    assert "__quantum__qis__h__body" in ir
    assert "__quantum__qis__cnot__body" in ir
    assert "__quantum__qis__mz__body" in ir


def autoqasm_bell_circuit():
    """Function that returns autoqasm bell circuit."""
    # pylint: disable-next=import-outside-toplevel
    from ..fixtures.autoqasm.circuits import autoqasm_bell

    return autoqasm_bell()


def qasm3_bell_reference():
    """Reference QASM3 string for Bell circuit"""
    return """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] __qubits__;
h __qubits__[0];
cx __qubits__[0], __qubits__[1];"""


@pytest.mark.skipif(not has_extra(autoqasm_to_qasm3), reason="Extra not installed")
def test_autoqasm_bell_to_qasm3_extra():
    """Test autoqasm-qasm3 conversion extra."""
    autoqasm_circuit = autoqasm_bell_circuit()
    conversions = [Conversion("autoqasm", "qasm3", autoqasm_to_qasm3)]
    graph = ConversionGraph(conversions)
    program = transpile(autoqasm_circuit, "qasm3", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, str)
    assert program == qasm3_bell_reference()


def autoqasm_shared15_circuit():
    """Function that returns autoqasm shared15 circuit."""
    # pylint: disable-next=import-outside-toplevel
    from ..fixtures.autoqasm.circuits import autoqasm_shared15

    return autoqasm_shared15()


def qasm3_shared15_reference():
    """Reference QASM3 string for shared15 circuit"""
    return """OPENQASM 3.0;
include "stdgates.inc";
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}
qubit[4] __qubits__;
h __qubits__[0];
h __qubits__[1];
h __qubits__[2];
h __qubits__[3];
x __qubits__[0];
x __qubits__[1];
y __qubits__[2];
z __qubits__[3];
s __qubits__[0];
sdg __qubits__[1];
t __qubits__[2];
tdg __qubits__[3];
rx(pi/4) __qubits__[0];
ry(pi/2) __qubits__[1];
rz(3*pi/4) __qubits__[2];
p(pi/8) __qubits__[3];
sx __qubits__[0];
sxdg __qubits__[1];
iswap __qubits__[2], __qubits__[3];
swap __qubits__[0], __qubits__[2];
swap __qubits__[1], __qubits__[3];
cx __qubits__[0], __qubits__[1];
cp(pi/4) __qubits__[2], __qubits__[3];"""


@pytest.mark.skipif(not has_extra(autoqasm_to_qasm3), reason="Extra not installed")
def test_autoqasm_shared15_to_qasm3_extra():
    """Test autoqasm-qasm3 conversion extra."""
    autoqasm_circuit = autoqasm_shared15_circuit()
    conversions = [Conversion("autoqasm", "qasm3", autoqasm_to_qasm3)]
    graph = ConversionGraph(conversions)
    program = transpile(autoqasm_circuit, "qasm3", conversion_graph=graph, max_path_depth=1)

    assert isinstance(program, str)
    assert program == normalize_qasm_gate_params(qasm3_shared15_reference())


def pennylane_bell_tape():
    """Returns a PennyLane QuantumTape for a Bell circuit."""
    from ..fixtures.pennylane.circuits import pennylane_bell  # pylint: disable=import-outside-toplevel

    return pennylane_bell()


# ---------------------------------------------------------------------------
# qiskit_to_pennylane
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not has_extra(qiskit_to_pennylane), reason="Extra not installed")
@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_qiskit_to_pennylane_extra_bell_and_wire_count(bell_circuit):
    """Test qiskit-pennylane conversion extra produces a QuantumTape and correct wires."""
    import pennylane  # pylint: disable=import-outside-toplevel

    qiskit_circuit, _ = bell_circuit
    conversions = [Conversion("qiskit", "pennylane", qiskit_to_pennylane)]
    graph = ConversionGraph(conversions)
    program = transpile(qiskit_circuit, "pennylane", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, pennylane.tape.QuantumTape)
    assert len(program.operations) == 2
    assert len(program.wires) == 2


# ---------------------------------------------------------------------------
# pennylane_to_qiskit
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not has_extra(pennylane_to_qiskit), reason="Extra not installed")
def test_pennylane_to_qiskit_extra_bell():
    """Test pennylane-qiskit conversion extra produces a QuantumCircuit (Bell circuit)."""
    import qiskit.circuit  # pylint: disable=import-outside-toplevel

    tape = pennylane_bell_tape()
    conversions = [Conversion("pennylane", "qiskit", pennylane_to_qiskit)]
    graph = ConversionGraph(conversions)
    program = transpile(tape, "qiskit", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, qiskit.circuit.QuantumCircuit)
    assert program.num_qubits == 2


@pytest.mark.skipif(not has_extra(pennylane_to_qiskit), reason="Extra not installed")
@pytest.mark.skipif(not has_extra(qiskit_to_pennylane), reason="Extra not installed")
def test_pennylane_qiskit_roundtrip_bell():
    """Test pennylane -> qiskit -> pennylane round-trip preserves operation count."""
    import pennylane  # pylint: disable=import-outside-toplevel

    tape = pennylane_bell_tape()
    conversions = [
        Conversion("pennylane", "qiskit", pennylane_to_qiskit),
        Conversion("qiskit", "pennylane", qiskit_to_pennylane),
    ]
    graph = ConversionGraph(conversions)
    qiskit_program = transpile(tape, "qiskit", conversion_graph=graph, max_path_depth=1)
    back = transpile(qiskit_program, "pennylane", conversion_graph=graph, max_path_depth=1)
    assert isinstance(back, pennylane.tape.QuantumTape)
    assert_allclose_up_to_global_phase(
        load_program(back).unitary(), load_program(tape).unitary(), atol=1e-7
    )


# ---------------------------------------------------------------------------
# pennylane_to_braket
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not has_extra(pennylane_to_braket), reason="Extra not installed")
def test_pennylane_to_braket_extra_bell():
    """Test pennylane-braket conversion extra produces a Braket Circuit (Bell circuit)."""
    tape = pennylane_bell_tape()
    conversions = [Conversion("pennylane", "braket", pennylane_to_braket)]
    graph = ConversionGraph(conversions)
    program = transpile(tape, "braket", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, braket.circuits.Circuit)
    assert program.qubit_count == 2
    # Bell circuit: H + CNOT = 2 instructions
    assert len(list(program.instructions)) == 2
    assert_allclose_up_to_global_phase(
        load_program(program).unitary(), load_program(tape).unitary(), atol=1e-7
    )


# ---------------------------------------------------------------------------
# pennylane_to_cirq
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not has_extra(pennylane_to_cirq), reason="Extra not installed")
def test_pennylane_to_cirq_extra_bell_and_qubit_count():
    """Test pennylane-cirq conversion extra produces a Cirq Circuit and correct qubit count."""
    import cirq  # pylint: disable=import-outside-toplevel

    tape = pennylane_bell_tape()
    conversions = [Conversion("pennylane", "cirq", pennylane_to_cirq)]
    graph = ConversionGraph(conversions)
    program = transpile(tape, "cirq", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, cirq.Circuit)
    assert len(program.all_qubits()) == 2
    assert_allclose_up_to_global_phase(
        load_program(program).unitary(), load_program(tape).unitary(), atol=1e-7
    )

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


from qbraid.passes.qasm.compat import normalize_qasm_gate_params
from qbraid.transpiler.conversions.qasm3 import autoqasm_to_qasm3
from qbraid.transpiler.conversions.qiskit import qiskit_to_braket, qiskit_to_ionq, qiskit_to_pyqir
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


@pytest.mark.skipif(not has_extra(qiskit_to_ionq), reason="Extra not installed")
def test_qiskit_to_ionq_preserves_declared_registers():
    """A circuit that was never transpiled keeps its register exactly.

    Idle qubits are part of the user's declared register -- IonQ measures every
    qubit, so narrowing to the used indices would change the width (and therefore
    the bitstring keys) of the results.
    """
    # pylint: disable=import-outside-toplevel
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3)
    qc.x(2)

    result = qiskit_to_ionq(qc, gateset="qis")

    assert result["qubits"] == 3
    assert result["circuit"][0]["targets"] == [2]


@pytest.mark.skipif(not has_extra(qiskit_to_ionq), reason="Extra not installed")
def test_qiskit_to_ionq_recovers_original_indices_from_layout():
    """A transpiled circuit is mapped back through its TranspileLayout.

    qiskit>=2 transpiled against a backend places a small circuit on the full
    physical topology. ``final_index_layout()`` is the exact inverse. The layout
    here maps virtual 0 -> physical 12 and virtual 1 -> physical 5: because
    12 > 5, compacting the *sorted* used indices would swap the two qubits, so
    this also pins that the mapping follows the layout rather than index order.
    """
    # pylint: disable=import-outside-toplevel
    from qiskit import QuantumCircuit
    from qiskit import transpile as qiskit_transpile
    from qiskit.transpiler import CouplingMap

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    transpiled = qiskit_transpile(
        qc,
        coupling_map=CouplingMap.from_full(20),
        initial_layout=[12, 5],
        optimization_level=0,
    )
    assert transpiled.num_qubits == 20 and transpiled.layout is not None

    result = qiskit_to_ionq(transpiled, gateset="qis")

    assert result["qubits"] == 2
    assert result["circuit"][0] == {"gate": "h", "targets": [0]}
    assert result["circuit"][1]["controls"] == [0]
    assert result["circuit"][1]["targets"] == [1]


@pytest.mark.skipif(not has_extra(qiskit_to_ionq), reason="Extra not installed")
def test_qiskit_to_ionq_idle_circuit_keeps_width():
    """A register with no gates still submits its declared width, not zero."""
    # pylint: disable=import-outside-toplevel
    from qiskit import QuantumCircuit

    result = qiskit_to_ionq(QuantumCircuit(2), gateset="qis")

    assert result["qubits"] == 2
    assert result["circuit"] == []


@pytest.mark.skipif(not has_extra(qiskit_to_ionq), reason="Extra not installed")
def test_qiskit_to_ionq_small_circuit_unchanged():
    """Test that qiskit_to_ionq produces correct output for a simple circuit
    that doesn't need remapping."""
    # pylint: disable=import-outside-toplevel
    import math

    from qiskit import QuantumCircuit

    qc = QuantumCircuit(1)
    qc.rx(-math.pi / 2, 0)

    result = qiskit_to_ionq(qc, gateset="qis")

    assert result["qubits"] == 1
    assert result["format"] == "ionq.circuit.v0"
    assert result["gateset"] == "qis"
    assert len(result["circuit"]) == 1
    assert result["circuit"][0]["gate"] == "rx"
    assert result["circuit"][0]["targets"] == [0]

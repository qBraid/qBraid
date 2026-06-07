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

# pylint: disable=redefined-outer-name

"""
Benchmarking tests for Qrisp conversions

"""

import importlib.util
import string

import numpy as np
import pytest
from cirq.contrib.qasm_import import circuit_from_qasm

from qbraid.interface import circuits_allclose
from qbraid.transpiler import ConversionGraph, transpile

try:
    import qrisp
    from qrisp.circuit.library import *  # pylint: disable=wildcard-import, unused-wildcard-import  # noqa: F403

    qrisp_not_installed = False
except ImportError:
    qrisp_not_installed = True

pytestmark = pytest.mark.skipif(qrisp_not_installed, reason="qrisp not installed")

np.random.seed(0)


gates_param_map = {
    "XGate": {"qubits": [0]},
    "YGate": {"qubits": [0]},
    "ZGate": {"qubits": [0]},
    "CXGate": {"qubits": [0, 1]},
    "CYGate": {"qubits": [0, 1]},
    "CZGate": {"qubits": [0, 1]},
    "MCXGate": {"qubits": [0, 1, 2, 3], "control_amount": 3},
    "PGate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "CPGate": {"qubits": [0, 1], "phi": np.random.rand() * 2 * np.pi},
    "u3Gate": {
        "qubits": [0],
        "theta": np.random.rand() * 2 * np.pi,
        "phi": np.random.rand() * 2 * np.pi,
        "lam": np.random.rand() * 2 * np.pi,
    },
    "HGate": {"qubits": [0]},
    "RXGate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "RYGate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "RZGate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "MCRXGate": {
        "qubits": [0, 1, 2, 3],
        "phi": np.random.rand() * 2 * np.pi,
        "control_amount": 3,
    },
    "SGate": {"qubits": [0]},
    "TGate": {"qubits": [0]},
    "RXXGate": {"qubits": [0, 1], "phi": np.random.rand() * 2 * np.pi},
    "RZZGate": {"qubits": [0, 1], "phi": np.random.rand() * 2 * np.pi},
    "SXGate": {"qubits": [0]},
    "SXDGGate": {"qubits": [0]},
    "XXYYGate": {"qubits": [0, 1]},
    "Barrier": {"qubits": [0]},
    "Measurement": {"qubits": [0], "clbits": [0]},
    "Reset": {"qubits": [0]},
    "QubitAlloc": {"qubits": [0]},
    "GPhaseGate": {"qubits": [0]},
    "SwapGate": {"qubits": [0, 1]},
    "U1Gate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "IDGate": {"qubits": [0]},
    "RGate": {
        "qubits": [0],
        "theta": np.random.rand() * 2 * np.pi,
        "phi": np.random.rand() * 2 * np.pi,
    },
}


@pytest.fixture
def qrisp_circuits():
    """Construct a dictionary of Qrisp circuits over all supported gates
    using random parameters as applicable.
    """
    qrisp_gates = {
        attr: None
        for attr in dir(qrisp.circuit.standard_operations)
        if attr[0] in string.ascii_uppercase
    }

    qrisp_gates.pop("Operation")
    qrisp_gates.pop("QubitAlloc")
    qrisp_gates.pop("QubitDealloc")
    qrisp_gates.pop("PauliGate")
    qrisp_gates.pop("Reset")

    # U3 gate is covered under `u3Gate` function
    qrisp_gates.pop("U3Gate")

    for gate in qrisp_gates:
        try:
            if gates_param_map[gate] is None:
                continue
            qubits = gates_param_map[gate]["qubits"]
            clbits = gates_param_map[gate]["clbits"] if "clbits" in gates_param_map[gate] else []
            gate_op = eval(gate)(  # pylint: disable=eval-used
                **{
                    key: gates_param_map[gate][key]
                    for key in gates_param_map[gate]
                    if key not in ["qubits", "clbits"]
                }
            )
            qc = qrisp.QuantumCircuit(gate_op.num_qubits, gate_op.num_clbits)
            qc.append(gate_op, qubits, clbits)
            qrisp_gates[gate] = qc  # type: ignore
        except Exception:  # pylint: disable=broad-exception-caught
            continue
    return qrisp_gates


@pytest.fixture
def conversion_graph():
    """Return a conversion graph of natively supported conversions."""
    return ConversionGraph(require_native=True)


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


ALL_TARGETS = [("cirq", 1.0), ("pytket", 1.0), ("qiskit", 1.0)]
AVAILABLE_TARGETS = [(name, version) for name, version in ALL_TARGETS if is_package_installed(name)]


def convert_from_qrisp_to_x(target, circuit_name, circuits, graph):
    """Construct a Qrisp circuit with the given gate, transpile it to
    target program type, and check equivalence.
    """
    source_circuit = circuits[circuit_name]
    circuit = transpile(source_circuit, target, conversion_graph=graph)
    circuit = transpile(circuit, "cirq", conversion_graph=graph)
    qasm = circuit.to_qasm()
    cirq_circuit = circuit_from_qasm(qasm)
    target_circuit = transpile(cirq_circuit, target)
    assert circuits_allclose(cirq_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), AVAILABLE_TARGETS)
def test_qrisp_coverage(target, baseline, qrisp_circuits, conversion_graph):
    """Test converting Qrisp circuits to supported target program type over
    all Qrisp gates and check against baseline expected accuracy.
    """
    ACCURACY_BASELINE = baseline
    ALLOWANCE = 0.01
    failures = {}
    for gate_name in qrisp_circuits:
        try:
            convert_from_qrisp_to_x(target, gate_name, qrisp_circuits, conversion_graph)
        except Exception as e:  # pylint: disable=broad-exception-caught
            failures[f"{target}-{gate_name}"] = e

    total_tests = len(qrisp_circuits)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails
    accuracy = float(nb_passes) / float(total_tests)

    assert accuracy >= ACCURACY_BASELINE - ALLOWANCE, (
        f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed "
        f"({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed "
        f"(expected >= {ACCURACY_BASELINE}).\nFailures: {failures.keys()}\n\n"
    )


@pytest.mark.parametrize("target", ["qasm2", "qasm3"])
def test_qrisp_to_qasm_roundtrip(target, conversion_graph):
    """Test forcing a roundtrip conversion from Qrisp to QASM and then to Cirq
    and check equivalence.
    """
    qc = qrisp.QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qasm = transpile(qc, target, conversion_graph=conversion_graph)
    assert isinstance(qasm, str)
    back = transpile(qasm, "cirq", conversion_graph=conversion_graph)
    assert circuits_allclose(qc.to_cirq(), back, strict_gphase=False)

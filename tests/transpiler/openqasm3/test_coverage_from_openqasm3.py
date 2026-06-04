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
Benchmarking tests for OpenQASM 3 (source) conversions.

"""

import importlib.util

import pytest

try:
    from qbraid.interface import circuits_allclose
    from qbraid.transpiler import ConversionGraph, transpile
    from qbraid.transpiler.conversions.qasm3 import qasm3_to_cirq

    cirq_not_installed = False
except ImportError:
    cirq_not_installed = True

# cirq is used as the equivalence reference (a raw QASM string has no unitary of its own)
pytestmark = pytest.mark.skipif(cirq_not_installed, reason="cirq not installed")


def _qasm(body: str, num_qubits: int) -> str:
    """Wrap a gate line in a minimal OpenQASM 3 program.

    The program declares exactly the number of qubits the gate acts on. This
    matters because the cirq reference parser prunes unused qubits while several
    target frameworks keep all declared qubits; declaring the minimum keeps the
    reference and the target circuits dimensionally comparable.
    """
    return "OPENQASM 3.0;\n" 'include "stdgates.inc";\n' f"qubit[{num_qubits}] q;\n" f"{body}\n"


# The OpenQASM 3 standard gate set (stdgates.inc). `cu` is omitted because the
# cirq reference parser rejects its 4-parameter form.
QASM_GATES = {
    "p": _qasm("p(0.5) q[0];", 1),
    "x": _qasm("x q[0];", 1),
    "y": _qasm("y q[0];", 1),
    "z": _qasm("z q[0];", 1),
    "h": _qasm("h q[0];", 1),
    "s": _qasm("s q[0];", 1),
    "sdg": _qasm("sdg q[0];", 1),
    "t": _qasm("t q[0];", 1),
    "tdg": _qasm("tdg q[0];", 1),
    "sx": _qasm("sx q[0];", 1),
    "rx": _qasm("rx(0.5) q[0];", 1),
    "ry": _qasm("ry(0.5) q[0];", 1),
    "rz": _qasm("rz(0.5) q[0];", 1),
    "cx": _qasm("cx q[0], q[1];", 2),
    "cy": _qasm("cy q[0], q[1];", 2),
    "cz": _qasm("cz q[0], q[1];", 2),
    "cp": _qasm("cp(0.5) q[0], q[1];", 2),
    "crx": _qasm("crx(0.5) q[0], q[1];", 2),
    "cry": _qasm("cry(0.5) q[0], q[1];", 2),
    "crz": _qasm("crz(0.5) q[0], q[1];", 2),
    "ch": _qasm("ch q[0], q[1];", 2),
    "swap": _qasm("swap q[0], q[1];", 2),
    "ccx": _qasm("ccx q[0], q[1], q[2];", 3),
    "cswap": _qasm("cswap q[0], q[1], q[2];", 3),
    "u": _qasm("u(0.1, 0.2, 0.3) q[0];", 1),
    "u1": _qasm("u1(0.5) q[0];", 1),
    "u2": _qasm("u2(0.1, 0.2) q[0];", 1),
    "u3": _qasm("u3(0.1, 0.2, 0.3) q[0];", 1),
    "id": _qasm("id q[0];", 1),
}


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


# (target, baseline). Baseline = measured coverage of openqasm3 -> target over the
# standard gate set, transpiled through a require-native conversion graph.
ALL_TARGETS = [
    ("pyquil", 1.0),
    ("qiskit", 1.0),
    ("cirq", 1.0),
    ("braket", 1.0),
    ("pytket", 1.0),
]
AVAILABLE_TARGETS = [(name, version) for name, version in ALL_TARGETS if is_package_installed(name)]

graph = ConversionGraph(require_native=True)


def convert_from_openqasm3_to_x(target, gate_name):
    """Transpile a single-gate OpenQASM 3 program to the target program type
    (via a require-native conversion graph) and check equivalence against a cirq
    reference."""
    qasm = QASM_GATES[gate_name]
    result = transpile(qasm, target, conversion_graph=graph)
    reference = qasm3_to_cirq(qasm)
    assert circuits_allclose(reference, result, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), AVAILABLE_TARGETS)
def test_openqasm3_coverage(target, baseline):
    """Measure openqasm3 -> target coverage over a standard gate set."""
    ACCURACY_BASELINE = baseline
    ALLOWANCE = 0.01
    failures = {}
    for gate_name in QASM_GATES:
        try:
            convert_from_openqasm3_to_x(target, gate_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            failures[f"{target}-{gate_name}"] = e

    total = len(QASM_GATES)
    nb_fails = len(failures)
    accuracy = (total - nb_fails) / total
    print(f"\n{target} coverage: {accuracy:.2%}  failures: {list(failures.keys())}")

    assert accuracy >= ACCURACY_BASELINE - ALLOWANCE, (
        f"Coverage threshold not met. {nb_fails}/{total} failed. " f"Failures: {failures.keys()}"
    )

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
    import pyquil  # pylint: disable=unused-import

    from qbraid.interface import circuits_allclose
    from qbraid.transpiler.conversions.openqasm3 import openqasm3_to_pyquil
    from qbraid.transpiler.conversions.qasm3 import qasm3_to_cirq

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def _qasm(body: str, num_qubits: int = 3) -> str:
    """Wrap a gate line in a minimal OpenQASM 3 program."""
    return "OPENQASM 3.0;\n" 'include "stdgates.inc";\n' f"qubit[{num_qubits}] q;\n" f"{body}\n"


# The OpenQASM 3 standard gate set (stdgates.inc). `cu` is omitted because the
# cirq reference parser rejects its 4-parameter form (it is still converted
# correctly by openqasm3_to_pyquil, just not benchmarkable against cirq here).
QASM_GATES = {
    "p": _qasm("p(0.5) q[0];"),
    "x": _qasm("x q[0];"),
    "y": _qasm("y q[0];"),
    "z": _qasm("z q[0];"),
    "h": _qasm("h q[0];"),
    "s": _qasm("s q[0];"),
    "sdg": _qasm("sdg q[0];"),
    "t": _qasm("t q[0];"),
    "tdg": _qasm("tdg q[0];"),
    "sx": _qasm("sx q[0];"),
    "rx": _qasm("rx(0.5) q[0];"),
    "ry": _qasm("ry(0.5) q[0];"),
    "rz": _qasm("rz(0.5) q[0];"),
    "cx": _qasm("cx q[0], q[1];"),
    "cy": _qasm("cy q[0], q[1];"),
    "cz": _qasm("cz q[0], q[1];"),
    "cp": _qasm("cp(0.5) q[0], q[1];"),
    "crx": _qasm("crx(0.5) q[0], q[1];"),
    "cry": _qasm("cry(0.5) q[0], q[1];"),
    "crz": _qasm("crz(0.5) q[0], q[1];"),
    "ch": _qasm("ch q[0], q[1];"),
    "swap": _qasm("swap q[0], q[1];"),
    "ccx": _qasm("ccx q[0], q[1], q[2];"),
    "cswap": _qasm("cswap q[0], q[1], q[2];"),
    "u": _qasm("u(0.1, 0.2, 0.3) q[0];"),
    "u1": _qasm("u1(0.5) q[0];"),
    "u2": _qasm("u2(0.1, 0.2) q[0];"),
    "u3": _qasm("u3(0.1, 0.2, 0.3) q[0];"),
    "id": _qasm("id q[0];"),
}


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


# (target, baseline). Baseline = measured coverage of openqasm3 -> target over the
# standard gate set (matches the @weight on openqasm3_to_pyquil).
ALL_TARGETS = [("pyquil", 1.0)]
AVAILABLE_TARGETS = [(n, v) for n, v in ALL_TARGETS if is_package_installed(n)]


def convert_from_openqasm3_to_x(target, gate_name):  # pylint: disable=unused-argument
    """Convert a single-gate OpenQASM 3 program to pyQuil and check equivalence
    against a cirq reference (raw QASM strings have no unitary method)."""
    qasm = QASM_GATES[gate_name]
    result = openqasm3_to_pyquil(qasm)
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

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
Benchmarking tests for OpenQASM 3 conversions.

"""
import importlib.util

import openqasm3
import pytest

from qbraid.interface import circuits_allclose
from qbraid.transpiler import ConversionGraph, transpile
from qbraid.transpiler.conversions.qasm3 import qasm3_to_cirq


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


OPENQASM3_GATE_STATEMENTS = {
    "x": "x q[0];",
    "y": "y q[0];",
    "z": "z q[0];",
    "h": "h q[0];",
    "s": "s q[0];",
    "sdg": "sdg q[0];",
    "t": "t q[0];",
    "tdg": "tdg q[0];",
    "sx": "sx q[0];",
    "rx": "rx(pi / 3) q[0];",
    "ry": "ry(pi / 4) q[0];",
    "rz": "rz(pi / 5) q[0];",
    "cx": "cx q[0], q[1];",
    "cz": "cz q[0], q[1];",
    "swap": "swap q[0], q[1];",
    "ccx": "ccx q[0], q[1], q[2];",
}

ALL_TARGETS = [("pyquil", 1.0)]
AVAILABLE_TARGETS = [
    (name, baseline) for name, baseline in ALL_TARGETS if is_package_installed(name)
]


def _openqasm3_program(gate_statement: str) -> str:
    return f"""
    OPENQASM 3.0;
    include "stdgates.inc";

    qubit[3] q;
    {gate_statement}
    """


def convert_from_openqasm3_to_x(target, gate_name, graph):
    """Construct an OpenQASM 3 AST program with the given gate and transpile it to target."""
    qasm = _openqasm3_program(OPENQASM3_GATE_STATEMENTS[gate_name])
    source_circuit = qasm3_to_cirq(qasm)
    target_circuit = transpile(openqasm3.parse(qasm), target, conversion_graph=graph)
    assert circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), AVAILABLE_TARGETS)
def test_openqasm3_coverage(target, baseline):
    """Test converting OpenQASM 3 programs to supported target program types."""
    graph = ConversionGraph(require_native=True)
    allowance = 0.01
    failures = {}
    for gate_name in OPENQASM3_GATE_STATEMENTS:
        try:
            convert_from_openqasm3_to_x(target, gate_name, graph)
        except Exception as err:  # pylint: disable=broad-exception-caught
            failures[f"{target}-{gate_name}"] = err

    total_tests = len(OPENQASM3_GATE_STATEMENTS)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails
    accuracy = float(nb_passes) / float(total_tests)

    assert accuracy >= baseline - allowance, (
        f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed "
        f"({nb_fails / total_tests:.2%}) and {nb_passes}/{total_tests} passed "
        f"(expected >= {baseline}).\nFailures: {failures.keys()}\n\n"
    )

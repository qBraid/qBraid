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
Benchmarking tests for conversions of circuits that contain measurements.

The per-package coverage modules (``test_coverage_from_*``) transpile single-gate
circuits with no measurements, so they score gate fidelity and are structurally blind
to how a conversion treats readout. That blind spot shipped a production failure:
``cirq -> pyquil`` splits the readout register into one ``BIT[1]`` declaration per
measurement key, and QCS rejects such programs with "Misplaced or illegal instruction
in ProtoQuil program". These tests transpile a measured GHZ circuit across every
reachable pair of supported program types and assert the readout structure survives.

"""
import importlib.util
import re

import pytest

from qbraid.transpiler import ConversionGraph, transpile

# GHZ on 3 qubits with a full-register measurement into one classical register --
# the shape qiskit's measure_all() and most user programs produce.
GHZ_QASM3 = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
bit[3] c;
h q[0];
cx q[0], q[1];
cx q[1], q[2];
c = measure q;
"""

NUM_QUBITS = 3

# Program types with unambiguous measurement semantics. Sorted so xdist workers agree.
MEASUREMENT_ALIASES = sorted(
    ["braket", "cirq", "openqasm3", "pyquil", "pytket", "qasm2", "qasm3", "qiskit"]
)

_ALIAS_PACKAGE = {"openqasm3": "openqasm3", "qasm2": "openqasm3", "qasm3": "openqasm3"}


def _installed(alias: str) -> bool:
    return importlib.util.find_spec(_ALIAS_PACKAGE.get(alias, alias)) is not None


def count_measurements(program, alias: str) -> int:
    """Count measurement operations in a program of the given type alias."""
    if alias in ("qasm2", "qasm3", "openqasm3"):
        # A register measurement ("c = measure q;") is one statement for N qubits;
        # unroll to per-qubit form so the count is qubits measured, not statements.
        import openqasm3  # pylint: disable=import-outside-toplevel
        import pyqasm  # pylint: disable=import-outside-toplevel

        if not isinstance(program, str):
            program = openqasm3.dumps(program)
        module = pyqasm.loads(program)
        module.unroll()
        return len(re.findall(r"\bmeasure\b", pyqasm.dumps(module)))
    if alias == "qiskit":
        return sum(1 for instr in program.data if instr.operation.name == "measure")
    if alias == "cirq":
        import cirq  # pylint: disable=import-outside-toplevel

        return sum(
            1
            for op in program.all_operations()
            if isinstance(op.gate, cirq.MeasurementGate)
            for _ in op.qubits
        )
    if alias == "braket":
        from braket.circuits import Measure  # pylint: disable=import-outside-toplevel

        return sum(1 for instr in program.instructions if isinstance(instr.operator, Measure))
    if alias == "pytket":
        import pytket.circuit  # pylint: disable=import-outside-toplevel

        return program.n_gates_of_type(pytket.circuit.OpType.Measure)
    if alias == "pyquil":
        return len([line for line in program.out().splitlines() if line.startswith("MEASURE")])
    raise ValueError(f"no measurement counter for '{alias}'")


def assert_pyquil_readout_intact(program) -> None:
    """Assert a pyQuil program declares a single contiguous readout register.

    One ``DECLARE <name> BIT[3]`` and three ``MEASURE`` instructions into it -- not one
    ``BIT[1]`` register per measurement, which is the fragmented form QCS translation
    rejects for hardware execution.
    """
    lines = program.out().splitlines()
    declares = [line for line in lines if line.startswith("DECLARE")]
    assert len(declares) == 1, f"readout register fragmented: {declares}"
    declared = re.fullmatch(rf"DECLARE (\S+) BIT\[{NUM_QUBITS}\]", declares[0])
    assert declared, f"unexpected readout declaration: {declares[0]!r}"
    register = declared.group(1)

    measures = [
        re.fullmatch(r"MEASURE \d+ (\S+)\[(\d+)\]", line)
        for line in lines
        if line.startswith("MEASURE")
    ]
    assert all(measures), "unparsable MEASURE instruction"
    targets = {m.group(1) for m in measures}
    assert targets == {register}, f"MEASURE targets {targets} != declared {register!r}"
    indices = sorted(int(m.group(2)) for m in measures)
    assert indices == list(range(NUM_QUBITS)), f"readout bits not distinct/complete: {indices}"


@pytest.fixture(scope="module")
def graph() -> ConversionGraph:
    """Conversion graph shared across the sweep."""
    return ConversionGraph()


# Pairs that do not currently preserve measurements, kept exact so drift in either
# direction fails loudly. A pair leaving this set is a fix: remove it here. A pair
# joining it is a regression: do not add it without understanding why.
KNOWN_MEASUREMENT_FAILURES: set[tuple[str, str]] = set()


@pytest.mark.parametrize("source", MEASUREMENT_ALIASES)
@pytest.mark.parametrize("target", MEASUREMENT_ALIASES)
def test_measured_circuit_survives_conversion(source, target, graph):
    """A measured GHZ circuit keeps its measurements through source -> target."""
    if source == target:
        pytest.skip("identity")
    if not (_installed(source) and _installed(target)):
        pytest.skip("source or target package not installed")
    if not (graph.has_path("qasm3", source) and graph.has_path(source, target)):
        pytest.skip("no conversion path")

    src_program = transpile(GHZ_QASM3, source, conversion_graph=graph)
    assert (
        count_measurements(src_program, source) == NUM_QUBITS
    ), f"building the {source} source circuit already lost measurements"

    out = transpile(src_program, target, conversion_graph=graph)
    n_measure = count_measurements(out, target)

    if (source, target) in KNOWN_MEASUREMENT_FAILURES:
        assert n_measure != NUM_QUBITS, (
            f"{source} -> {target} now preserves measurements; "
            "remove it from KNOWN_MEASUREMENT_FAILURES"
        )
        return

    assert (
        n_measure == NUM_QUBITS
    ), f"{source} -> {target}: expected {NUM_QUBITS} measurements, found {n_measure}"
    if target == "pyquil":
        assert_pyquil_readout_intact(out)

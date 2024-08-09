# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Benchmarking tests for PyTKET conversions

"""
import importlib.util
import string

import numpy as np
import pytest
from cirq.contrib.qasm_import import circuit_from_qasm

from qbraid.interface import circuits_allclose
from qbraid.transpiler import ConversionGraph, transpile

try:
    import pytket

    pytket_not_installed = False
except ImportError:
    pytket_not_installed = True

pytestmark = pytest.mark.skipif(pytket_not_installed, reason="pytket not installed")

np.random.seed(0)

# TODO: Investigate generating params dynamically.
# Difficult because pytket methods are wrapped around C++ code.
gates_param_map = {
    "H": {"qubit": 0},
    "S": {"qubit": 0},
    "SX": {"qubit": 0},
    "SXdg": {"qubit": 0},
    "Sdg": {"qubit": 0},
    "T": {"qubit": 0},
    "Tdg": {"qubit": 0},
    "V": {"qubit": 0},
    "Vdg": {"qubit": 0},
    "X": {"qubit": 0},
    "Y": {"qubit": 0},
    "Z": {"qubit": 0},
    "Phase": {"arg0": np.random.rand() * 2 * np.pi},
    "Rx": {"angle": np.random.rand() * 2 * np.pi, "qubit": 0},
    "Ry": {"angle": np.random.rand() * 2 * np.pi, "qubit": 0},
    "Rz": {"angle": np.random.rand() * 2 * np.pi, "qubit": 0},
    "U1": {"angle": np.random.rand() * 2 * np.pi, "qubit": 0},
    "ECR": {"qubit_0": 0, "qubit_1": 1},
    "SWAP": {"qubit_0": 0, "qubit_1": 1},
    "ISWAPMax": {"qubit0": 0, "qubit1": 1},
    "Sycamore": {"qubit0": 0, "qubit1": 1},
    "ZZMax": {"qubit0": 0, "qubit1": 1},
    "CH": {"control_qubit": 0, "target_qubit": 1},
    "CSX": {"control_qubit": 0, "target_qubit": 1},
    "CSXdg": {"control_qubit": 0, "target_qubit": 1},
    "CV": {"control_qubit": 0, "target_qubit": 1},
    "CVdg": {"control_qubit": 0, "target_qubit": 1},
    "CX": {"control_qubit": 0, "target_qubit": 1},
    "CY": {"control_qubit": 0, "target_qubit": 1},
    "CZ": {"control_qubit": 0, "target_qubit": 1},
    "CCX": {"control_0": 0, "control_1": 1, "target": 2},
    "CSWAP": {"control": 0, "target_0": 1, "target_1": 2},
    "Measure": {"qubit": 0, "bit_index": 0},
    "CRx": {"angle": np.random.rand() * 2 * np.pi, "control_qubit": 0, "target_qubit": 1},
    "CRy": {"angle": np.random.rand() * 2 * np.pi, "control_qubit": 0, "target_qubit": 1},
    "CRz": {"angle": np.random.rand() * 2 * np.pi, "control_qubit": 0, "target_qubit": 1},
    "CU1": {"angle": np.random.rand() * 2 * np.pi, "control_qubit": 0, "target_qubit": 1},
    "CU3": {
        "angle0": np.random.rand() * 2 * np.pi,
        "angle1": np.random.rand() * 2 * np.pi,
        "angle2": np.random.rand() * 2 * np.pi,
        "control_qubit": 0,
        "target_qubit": 1,
    },
    "ESWAP": {"angle": np.random.rand() * 2 * np.pi, "qubit0": 0, "qubit1": 1},
    "ISWAP": {"angle": np.random.rand() * 2 * np.pi, "qubit0": 0, "qubit1": 1},
    "FSim": {
        "angle0": np.random.rand() * 2 * np.pi,
        "angle1": np.random.rand() * 2 * np.pi,
        "qubit0": 0,
        "qubit1": 1,
    },
    "PhasedISWAP": {
        "angle0": np.random.rand() * 2 * np.pi,
        "angle1": np.random.rand() * 2 * np.pi,
        "qubit0": 0,
        "qubit1": 1,
    },
    "PhasedX": {
        "angle0": np.random.rand() * 2 * np.pi,
        "angle1": np.random.rand() * 2 * np.pi,
        "qubit": 0,
    },
    "U2": {
        "angle0": np.random.rand() * 2 * np.pi,
        "angle1": np.random.rand() * 2 * np.pi,
        "qubit": 0,
    },
    "TK1": {
        "angle0": np.random.rand() * 2 * np.pi,
        "angle1": np.random.rand() * 2 * np.pi,
        "angle2": np.random.rand() * 2 * np.pi,
        "qubit": 0,
    },
    "U3": {
        "angle0": np.random.rand() * 2 * np.pi,
        "angle1": np.random.rand() * 2 * np.pi,
        "angle2": np.random.rand() * 2 * np.pi,
        "qubit": 0,
    },
    "TK2": {
        "angle0": np.random.rand() * 2 * np.pi,
        "angle1": np.random.rand() * 2 * np.pi,
        "angle2": np.random.rand() * 2 * np.pi,
        "qubit0": 0,
        "qubit1": 1,
    },
    "XXPhase": {"angle": np.random.rand() * 2 * np.pi, "qubit0": 0, "qubit1": 1},
    "YYPhase": {"angle": np.random.rand() * 2 * np.pi, "qubit0": 0, "qubit1": 1},
    "ZZPhase": {"angle": np.random.rand() * 2 * np.pi, "qubit0": 0, "qubit1": 1},
    "XXPhase3": {"angle": np.random.rand() * 2 * np.pi, "qubit0": 0, "qubit1": 1, "qubit2": 2},
}


@pytest.fixture
def pytket_circuits():
    """Construct a dictionary of PyTKET circuits over all supported gates
    using random parameters as applicable.
    """
    pytket_gates = {attr: None for attr in dir(pytket.Circuit) if attr[0] in string.ascii_uppercase}
    for gate in pytket_gates:
        try:
            if gates_param_map[gate] is None:
                continue
            pytket_gates[gate] = getattr(pytket.Circuit(3, 1), gate)(**gates_param_map[gate])
        except Exception:  # pylint: disable=broad-exception-caught
            continue
    return {k: v for k, v in pytket_gates.items() if v is not None}


@pytest.fixture
def conversion_graph():
    """Return a conversion graph of natively supported conversions."""
    return ConversionGraph(require_native=True)


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


ALL_TARGETS = [("braket", 0.64), ("cirq", 0.66), ("pyquil", 0.66), ("qiskit", 0.66)]
AVAILABLE_TARGETS = [(name, version) for name, version in ALL_TARGETS if is_package_installed(name)]


def convert_from_pytket_to_x(target, circuit_name, circuits, graph):
    """Construct a PyTKET circuit with the given gate, transpile it to
    target program type, and check equivalence.
    """
    source_circuit = circuits[circuit_name]
    circuit = transpile(source_circuit, "cirq", conversion_graph=graph)
    qasm = circuit.to_qasm()
    cirq_circuit = circuit_from_qasm(qasm)
    target_circuit = transpile(cirq_circuit, target)
    assert circuits_allclose(cirq_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), AVAILABLE_TARGETS)
def test_pytket_coverage(target, baseline, pytket_circuits, conversion_graph):
    """Test converting PyTKET circuits to supported target program type over
    all PyTKET gates and check against baseline expecte accuracy.
    """
    ACCURACY_BASELINE = baseline
    ALLOWANCE = 0.01
    failures = {}
    for gate_name in pytket_circuits:
        try:
            convert_from_pytket_to_x(target, gate_name, pytket_circuits, conversion_graph)
        except Exception as e:  # pylint: disable=broad-exception-caught
            failures[f"{target}-{gate_name}"] = e

    total_tests = len(pytket_circuits)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails
    accuracy = float(nb_passes) / float(total_tests)

    assert accuracy >= ACCURACY_BASELINE - ALLOWANCE, (
        f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed "
        f"({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed "
        f"(expected >= {ACCURACY_BASELINE}).\nFailures: {failures.keys()}\n\n"
    )

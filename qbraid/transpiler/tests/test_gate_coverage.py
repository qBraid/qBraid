# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Gate coverage tests for the qbraid transpiler.

"""
import cirq
import numpy as np
import pytest
from cirq import Circuit as CirqCircuit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.cirq_braket.convert_to_braket import to_braket
from qbraid.transpiler.cirq_pyquil.conversions import to_pyquil
from qbraid.transpiler.cirq_pytket.conversions import to_pytket
from qbraid.transpiler.cirq_qasm.tests._gate_archive import cirq_gates, create_cirq_gate
from qbraid.transpiler.cirq_qiskit.conversions import to_qiskit
from qbraid.transpiler.tests.test_transpiler import nqubits_nparams

gates_coverage = {
    "cirq_to_qiskit": 0,
    "qiskit_to_cirq": 0,
    "cirq_to_braket": 0,
    "braket_to_cirq": 0,
    "cirq_to_pyquil": 0,
    "pyquil_to_cirq": 0,
    "cirq_to_pytket": 0,
    "pytket_to_cirq": 0,
}

gate_failures = {
    "cirq_to_qiskit": [],
    "qiskit_to_cirq": [],
    "cirq_to_braket": [],
    "braket_to_cirq": [],
    "cirq_to_pyquil": [],
    "pyquil_to_cirq": [],
    "cirq_to_pytket": [],
    "pytket_to_cirq": [],
}


def _assign_params_cirq(gate_str, nparams):
    params = np.random.random_sample(nparams) * np.pi
    cirq_data = {"type": gate_str, "params": params, "matrix": None}
    new_cirq_gate = create_cirq_gate(cirq_data)
    return new_cirq_gate


def _construct_gate_circuit(test_gate, nqubits):
    circuit = CirqCircuit()
    q2, q1, q0 = [cirq.LineQubit(i) for i in range(3)]

    if nqubits == 1:
        input_qubits = [q0]
    elif nqubits == 2:
        input_qubits = [q0, q1]
    else:
        input_qubits = [q0, q1, q2]

    cirq_gate_test_gates = [
        test_gate(*input_qubits),
    ]

    for gate in cirq_gate_test_gates:
        circuit.append(gate)
    return circuit


def _build_cirq_gate_circuits(gate_set):
    circuit_map = {}

    for gate_str in gate_set:
        nqubits, nparams = nqubits_nparams(gate_str)
        cirq_gate = _assign_params_cirq(gate_str, nparams)
        cirq_circuit = _construct_gate_circuit(cirq_gate, nqubits)

        circuit_map[gate_str] = cirq_circuit
    return circuit_map


# Cirq
cirq_gate_set = set(cirq_gates.keys())
cirq_gate_circuits = _build_cirq_gate_circuits(cirq_gate_set)

# Qiskit (TO DO)

# Braket (TO DO)

# Pyquil (TO DO)

# Pytket (TO DO)


# cirq to braket
@pytest.mark.parametrize("cirq_gate_str", cirq_gate_set)
def test_coverage_cirq_to_qiskit(cirq_gate_str):
    try:
        cirq_circuit = cirq_gate_circuits[cirq_gate_str]
        qiskit_circuit = to_qiskit(cirq_circuit)
        if circuits_allclose(cirq_circuit, qiskit_circuit, strict_gphase=False):
            gates_coverage["cirq_to_qiskit"] += 1
        else:
            gate_failures["cirq_to_qiskit"].append((cirq_gate_str, e))
    except Exception as e:
        gate_failures["cirq_to_qiskit"].append((cirq_gate_str, e))


# cirq to braket
@pytest.mark.parametrize("cirq_gate_str", cirq_gate_set)
def test_coverage_cirq_to_braket(cirq_gate_str):
    try:
        cirq_circuit = cirq_gate_circuits[cirq_gate_str]
        braket_circuit = to_braket(cirq_circuit)
        if circuits_allclose(cirq_circuit, braket_circuit, strict_gphase=False):
            gates_coverage["cirq_to_braket"] += 1
        else:
            gate_failures["cirq_to_braket"].append((cirq_gate_str, e))
    except Exception as e:
        gate_failures["cirq_to_braket"].append((cirq_gate_str, e))


# cirq to pyquil
@pytest.mark.parametrize("cirq_gate_str", cirq_gate_set)
def test_coverage_cirq_to_pyquil(cirq_gate_str):
    try:
        cirq_circuit = cirq_gate_circuits[cirq_gate_str]
        pyquil_circuit = to_pyquil(cirq_circuit)
        if circuits_allclose(cirq_circuit, pyquil_circuit, strict_gphase=False):
            gates_coverage["cirq_to_pyquil"] += 1
        else:
            gate_failures["cirq_to_pyquil"].append((cirq_gate_str, e))
    except Exception as e:
        gate_failures["cirq_to_pyquil"].append((cirq_gate_str, e))


# cirq to pytket
@pytest.mark.parametrize("cirq_gate_str", cirq_gate_set)
def test_coverage_cirq_to_pytket(cirq_gate_str):
    try:
        cirq_circuit = cirq_gate_circuits[cirq_gate_str]
        pytket_circuit = to_pytket(cirq_circuit)
        if circuits_allclose(cirq_circuit, pytket_circuit, strict_gphase=False):
            gates_coverage["cirq_to_pytket"] += 1
        else:
            gate_failures["cirq_to_pytket"].append((cirq_gate_str, e))
    except Exception as e:
        gate_failures["cirq_to_pytket"].append((cirq_gate_str, e))


# braket to cirq  (TO DO)

# pyquil to cirq  (TO DO)

# pytket to cirq  (TO DO)


def test_coverage():
    print("Gate coverage: ", gates_coverage)
    print("Gate failures: ", gate_failures)

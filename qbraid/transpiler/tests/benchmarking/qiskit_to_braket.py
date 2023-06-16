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
Benchmarking accuracy of qiskit to braket conversions

"""
import string

import numpy as np
import qiskit
import qiskit_braket_provider

import qbraid


def generate_params(varnames, seed=0):
    np.random.seed(seed)
    params = {
        ra: np.random.rand() * 2 * np.pi
        for ra in ["theta", "phi", "lam", "gamma"]
        if ra in varnames
    }
    if "num_ctrl_qubits" in varnames:
        params["num_ctrl_qubits"] = np.random.randint(1, 7)
    if "phase" in varnames:
        params["phase"] = np.random.rand() * 2 * np.pi
    return params


def get_qiskit_gates():
    qiskit_gates = {
        attr: None
        for attr in dir(qiskit.circuit.library.standard_gates)
        if attr[0] in string.ascii_uppercase
    }
    for gate in qiskit_gates:
        params = generate_params(
            getattr(qiskit.circuit.library.standard_gates, gate).__init__.__code__.co_varnames
        )
        qiskit_gates[gate] = getattr(qiskit.circuit.library.standard_gates, gate)(**params)
    return {k: v for k, v in qiskit_gates.items() if v is not None}


def execute_test(conversion_function, qiskit_circuit):
    try:
        braket_circuit = conversion_function(qiskit_circuit)
        if not qbraid.interface.circuits_allclose(
            qiskit_circuit, braket_circuit, strict_gphase=False
        ):
            return 1
    except Exception:
        return 1
    return 0


qiskit_gates = get_qiskit_gates()
qbraid_failed, qiskit_failed = 0, 0

for gate_name, gate in qiskit_gates.items():
    qiskit_circuit = qiskit.QuantumCircuit(gate.num_qubits)
    qiskit_circuit.compose(gate, inplace=True)

    qiskit_failed += execute_test(
        qiskit_braket_provider.providers.adapter.convert_qiskit_to_braket_circuit, qiskit_circuit
    )
    qbraid_failed += execute_test(
        lambda circuit: qbraid.circuit_wrapper(circuit).transpile("braket"), qiskit_circuit
    )

total_tests = len(qiskit_gates)
qbraid_passed, qiskit_passed = total_tests - qbraid_failed, total_tests - qiskit_failed
qbraid_percentage, qiskit_percentage = round((qbraid_passed / total_tests) * 100, 2), round(
    (qiskit_passed / total_tests) * 100, 2
)

print(f"Qiskit to Braket standard gate conversion tests\n")
print(f"qbraid: {qbraid_passed}/{total_tests} ~= {qbraid_percentage}%")
print(f"qiskit-braket-provider: {qiskit_passed}/{total_tests} ~= {qiskit_percentage}%")

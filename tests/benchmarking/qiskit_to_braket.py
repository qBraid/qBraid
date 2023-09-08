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
import qiskit
import qiskit_braket_provider

import qbraid

from .._data.qiskit.gates import get_qiskit_gates


def execute_test(conversion_function, input_circuit):
    """Execute conversion, test equality, and return 1 if it fails, 0 otherwise"""
    try:
        output_circuit = conversion_function(input_circuit)
        if not qbraid.interface.circuits_allclose(
            input_circuit, output_circuit, strict_gphase=False
        ):
            return 1
    except Exception:  # pylint: disable=broad-exception-caught
        return 1
    return 0


qiskit_gates = get_qiskit_gates(seed=0)
qbraid_failed, qiskit_failed = 0, 0

for gate_name, gate in qiskit_gates.items():
    if gate_name == "GlobalPhaseGate":
        continue

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

print("Qiskit to Braket standard gate conversion tests\n")
print(f"qbraid: {qbraid_passed}/{total_tests} ~= {qbraid_percentage}%")  # 58/58
print(f"qiskit-braket-provider: {qiskit_passed}/{total_tests} ~= {qiskit_percentage}%")  # 31/58

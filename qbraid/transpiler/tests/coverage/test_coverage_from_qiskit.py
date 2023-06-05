# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
import string

import numpy as np
import pytest
import qiskit

import qbraid

#############
### UTILS ###
#############


def generate_params(varnames):
    params = {}
    rot_args = ["theta", "phi", "lam", "gamma"]
    for ra in rot_args:
        if ra in varnames:
            params[ra] = np.random.rand() * 2 * np.pi
    if "num_ctrl_qubits" in varnames:
        params["num_ctrl_qubits"] = np.random.randint(1, 7)
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


#############
### TESTS ###
#############

TARGETS = ["braket", "cirq", "pyquil", "pytket"]
qiskit_gates = get_qiskit_gates()
paramslist = [(target, gate) for target in TARGETS for gate in qiskit_gates]


@pytest.mark.parametrize("target, gate_name", paramslist)
def test_convert_from_qiskit_to_x(target, gate_name):
    gate = qiskit_gates[gate_name]
    source_circuit = qiskit.QuantumCircuit(gate.num_qubits)
    source_circuit.compose(gate, inplace=True)
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)

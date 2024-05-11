# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for Cirq gate dictionary used for testing

"""
import numpy as np
from cirq.ops.common_gates import (
    CXPowGate,
    CZPowGate,
    HPowGate,
    XPowGate,
    YPowGate,
    ZPowGate,
    cphase,
    rx,
    ry,
    rz,
)
from cirq.ops.identity import IdentityGate
from cirq.ops.matrix_gates import MatrixGate
from cirq.ops.swap_gates import ISwapPowGate, SwapPowGate
from cirq.ops.three_qubit_gates import CCXPowGate, CCZPowGate

from qbraid.transpiler.conversions.braket.braket_to_cirq import _give_cirq_gate_name
from qbraid.transpiler.conversions.qasm2.cirq_custom import U3Gate

cirq_gates = {
    "H": HPowGate,
    "X": XPowGate,
    "Y": YPowGate,
    "Z": ZPowGate,
    "S": ZPowGate,
    "T": ZPowGate,
    "I": IdentityGate,
    "HPow": HPowGate,
    "XPow": XPowGate,
    "YPow": YPowGate,
    "ZPow": ZPowGate,
    "RX": rx,
    "RY": ry,
    "RZ": rz,
    "Phase": ZPowGate,
    "U1": ZPowGate,
    "CX": CXPowGate,
    "Swap": SwapPowGate,
    "iSwap": ISwapPowGate,
    "CZ": CZPowGate,
    "CPhase": cphase,
    "CCZ": CCZPowGate,
    "CCX": CCXPowGate,
    "U3": U3Gate,
}


def create_cirq_gate(data):
    gate_type = data["type"]
    params = data["params"]
    matrix = data["matrix"]

    # single-qubit, no parameters
    if gate_type in ("H", "X", "Y", "Z"):
        return cirq_gates[gate_type]()

    elif gate_type == "I":
        return cirq_gates["I"](num_qubits=1)

    elif gate_type == "S":
        return cirq_gates["S"](exponent=0.5)
    elif gate_type == "T":
        return cirq_gates["T"](exponent=0.25)

    # single-qubit, one-parameter gates
    elif gate_type in ("RX", "RY", "RZ"):
        theta = data["params"][0]
        # theta = data["params"][0] / np.pi
        return cirq_gates[gate_type](theta)

    elif gate_type in ("HPow", "XPow", "YPow", "ZPow"):
        exponent = data["params"][0]
        return cirq_gates[gate_type](exponent=exponent)

    elif gate_type in ("Phase", "U1"):
        t = data["params"][0] / np.pi
        return cirq_gates["Phase"](exponent=t)

    # two-qubit, no parameters
    elif gate_type in ("CX", "CZ"):
        return cirq_gates[gate_type]()  # default exponent = 1

    elif gate_type in "CPhase":
        return cirq_gates[gate_type](data["params"][0])

    elif gate_type in ("Swap", "iSwap"):
        return cirq_gates[gate_type](exponent=1.0)

    # multi-qubit
    elif gate_type in "CCX":
        return cirq_gates[gate_type]()

    # custom gates
    elif gate_type == "U3":
        return U3Gate(*params)

    elif gate_type == "Unitary" or matrix is not None:
        n_qubits = int(np.log2(len(matrix)))
        unitary_gate = MatrixGate(matrix)
        _give_cirq_gate_name(unitary_gate, "U", n_qubits)
        return unitary_gate

    else:
        raise ValueError(f"Gate of type {gate_type} not supported for Cirq testing.")

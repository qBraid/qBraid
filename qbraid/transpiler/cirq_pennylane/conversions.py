# Copyright 2023 qBraid
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
Module containing functions to convert between Cirq's circuit
representation and Pennylane's circuit representation.

"""
from cirq import Circuit
from pennylane import from_qasm as pennylane_from_qasm
from pennylane.tape import QuantumTape
from pennylane.wires import Wires
from pennylane_qiskit.qiskit_device import QISKIT_OPERATION_MAP

from qbraid.transpiler.cirq_utils import from_qasm as cirq_from_qasm
from qbraid.transpiler.cirq_utils import to_qasm

SUPPORTED_PL = set(QISKIT_OPERATION_MAP.keys())
UNSUPPORTED = {"CRX", "CRY", "CRZ", "S", "T"}
SUPPORTED = SUPPORTED_PL - UNSUPPORTED


class UnsupportedQuantumTapeError(Exception):
    """Class for exceptions raised processing unsupported quantum tape objects"""


def from_pennylane(tape: QuantumTape) -> Circuit:
    """Returns a Cirq circuit equivalent to the input QuantumTape.

    Args:
        tape: Pennylane QuantumTape to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input QuantumTape.
    """
    try:
        wires = sorted(tape.wires)
    except TypeError as err:
        raise UnsupportedQuantumTapeError(
            f"The wires of the tape must be sortable, but could not sort " f"{tape.wires}."
        ) from err

    for index, wire in enumerate(wires):
        if wire != index:
            raise UnsupportedQuantumTapeError(
                "The wire labels of the tape must contiguously pack 0 to n-1, for n wires."
            )

    if len(tape.measurements) > 0:
        raise UnsupportedQuantumTapeError(
            "Measurements are not supported on the input tape. "
            "They should be subsequently added by the executor."
        )

    tape = tape.expand(stop_at=lambda obj: obj.name in SUPPORTED)
    qasm = tape.to_openqasm(rotations=False, wires=wires, measure_all=False)

    return cirq_from_qasm(qasm)


def to_pennylane(circuit: Circuit) -> QuantumTape:
    """Returns a QuantumTape equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a Pennylane QuantumTape.

    Returns:
        QuantumTape object equivalent to the input Cirq circuit.
    """
    qfunc = pennylane_from_qasm(to_qasm(circuit))

    with QuantumTape() as tape:
        qfunc(wires=Wires(range(len(circuit.all_qubits()))))

    return tape

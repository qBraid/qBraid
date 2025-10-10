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
Module for generating random IonQ programs

"""
from typing import Optional

import numpy as np

from qbraid.programs.gate_model.ionq import IonQProgram
from qbraid.programs.typer import IonQDict
from qbraid.transpiler import transpile

from .qasm3_random import qasm3_random_from_gates


def create_gateset_ionq(max_operands: int) -> np.ndarray:
    """Gets QASM for IonQ gateset with max_operands."""
    q1_gates: list[tuple[str, int, int]] = [
        ("x", 1, 0),
        ("y", 1, 0),
        ("z", 1, 0),
        ("h", 1, 0),
        ("s", 1, 0),
        ("t", 1, 0),
        ("v", 1, 0),
        ("si", 1, 0),
        ("ti", 1, 0),
        ("vi", 1, 0),
        ("rx", 1, 1),
        ("ry", 1, 1),
        ("rz", 1, 1),
    ]

    q2_gates: list[tuple[str, int, int]] = [
        ("cx", 2, 0),
        ("cy", 2, 0),
        ("cz", 2, 0),
        ("ch", 2, 0),
        ("crx", 2, 1),
        ("cry", 2, 1),
        ("crz", 2, 1),
        ("swap", 2, 0),
    ]

    q3_gates: list[tuple[str, int, int]] = [("ccnot", 3, 0)]

    gates = q1_gates.copy()

    if max_operands >= 2:
        gates.extend(q2_gates)
    if max_operands >= 3:
        gates.extend(q3_gates)

    gates_array = np.array(
        gates, dtype=[("gate", object), ("num_qubits", np.int64), ("num_params", np.int64)]
    )
    return gates_array


def ionq_random(
    num_qubits: Optional[int] = None,
    depth: Optional[int] = None,
    max_operands: Optional[int] = None,
    seed: Optional[int] = None,
) -> IonQDict:
    """Generate random OpenQASM 3 program.

    Args:
        num_qubits (int): Number of quantum wires.
        depth (int): Layers of operations (i.e., critical path length).
        max_operands (int): Maximum size of gate for each operation.
        seed (int): Seed for random number generator.
        measure (bool): Whether to include measurement gates.

    Raises:
        ValueError: When invalid random circuit options are given,
            or fails to generate valid IonQDict
        QbraidError: When failed to create random OpenQASM 3 program.

    Returns:
        IonQDict: Random IonQ program
    """
    qasm3_program = qasm3_random_from_gates(
        create_gateset_ionq, num_qubits, depth, max_operands, seed, False
    )

    ionq_dict = transpile(qasm3_program, "ionq")

    ionq_program = IonQProgram(ionq_dict)

    ionq_program.validate_for_gateset()

    return ionq_dict

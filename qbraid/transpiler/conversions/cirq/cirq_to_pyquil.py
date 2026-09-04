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
Module containing function to convert from Cirq's circuit
representation to pyQuil's circuit representation (Quil programs).

"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from cirq import LineQubit, QubitOrder, parameter_names
from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

try:
    from .cirq_quil_output import QuilOutput
except ImportError:  # pragma: no cover
    QuilOutput = None

pyquil = LazyLoader("pyquil", globals(), "pyquil")

if TYPE_CHECKING:
    import cirq.circuits
    from pyquil import Program

# ``pyquil_to_cirq`` names a slot of a declared register ``name[offset]``, and the bare
# ``name`` when the register holds exactly one value. This recovers the register sizes
# from those symbol names.
_SLOT = re.compile(r"([A-Za-z_]\w*)\[(\d+)\]")


def _declared_registers(circuit: cirq.circuits.Circuit) -> dict[str, int]:
    """Maps each free parameter's register name to the size needed to declare it."""
    sizes: dict[str, int] = {}
    for symbol in sorted(str(name) for name in parameter_names(circuit)):
        match = _SLOT.fullmatch(symbol)
        name, size = (match.group(1), int(match.group(2)) + 1) if match else (symbol, 1)
        sizes[name] = max(sizes.get(name, 0), size)
    return sizes


@weight(0.74)
def cirq_to_pyquil(circuit: cirq.circuits.Circuit) -> Program:
    """Returns a pyQuil Program equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a pyQuil Program.

    Returns:
        pyquil.Program object equivalent to the input Cirq circuit.
    """
    input_qubits = circuit.all_qubits()
    max_qubit = max(input_qubits)
    # if we are using LineQubits, keep the qubit labeling the same
    if isinstance(max_qubit, LineQubit):
        qubit_range = max_qubit.x + 1
        qubit_order = LineQubit.range(qubit_range)
    # otherwise, use the default ordering (starting from zero)
    else:
        qubit_order = QubitOrder.DEFAULT
    qubits = QubitOrder.as_qubit_order(qubit_order).order_for(input_qubits)
    operations = circuit.all_operations()
    try:
        quil_str = str(QuilOutput(operations, qubits))
        program = pyquil.Program(quil_str)
    except ValueError as err:
        raise ProgramConversionError(
            f"Cirq qasm converter doesn't yet support {err.args[0][32:]}."
        ) from err

    # A free parameter appears in the gate lines but has no ``DECLARE``, so the emitted
    # program is not valid Quil on its own and does not survive a round trip: re-parsing
    # leaves the register undeclared, and ``pyquil_to_cirq``'s size lookup then reads
    # slot 0 as the bare register name -- so ``thetas[0]`` comes back as ``thetas`` while
    # ``thetas[1]`` keeps its index, naming one register two ways.
    declarations = pyquil.Program()
    for name, size in _declared_registers(circuit).items():
        declarations.declare(name, "REAL", size)
    return declarations + program if declarations else program

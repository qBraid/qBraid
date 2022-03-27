# Copyright (C) 2020 Unitary Fund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Defines input / output types for a quantum backend:

  * SUPPORTED_PROGRAM_TYPES: All supported packages/circuits which
       the qbraid.transpiler can interface with,
  * QPROGRAM: All supported packages / circuits which are installed in the
       environment the qbraid.transpiler is run in, and
"""
from typing import Union

from braket.circuits import Circuit as _BKCircuit
from cirq import Circuit as _Circuit
from pennylane.tape import QuantumTape as _QuantumTape
from pyquil import Program as _Program
from qiskit import QuantumCircuit as _QuantumCircuit

# Supported quantum programs.
SUPPORTED_PROGRAM_TYPES = {
    "cirq": "Circuit",
    "pyquil": "Program",
    "qiskit": "QuantumCircuit",
    "braket": "Circuit",
    "pennylane": "QuantumTape",
}

# Supported quantum programs.
QPROGRAM = Union[_Circuit, _Program, _QuantumCircuit, _BKCircuit, _QuantumTape]

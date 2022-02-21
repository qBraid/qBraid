# Copyright (C) 2021 Unitary Fund
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

"""Qiskit utility functions."""
import numpy as np

from cirq import Circuit

from qiskit import QuantumCircuit

from qbraid.interface import to_unitary


def _equal_unitaries(qiskit_circuit: QuantumCircuit, cirq_circuit: Circuit):
    """Returns True if Qiskit circuit unitary and Cirq circuit
    unitary are equivalent."""
    qiskit_u = to_unitary(qiskit_circuit)
    cirq_u = to_unitary(cirq_circuit, ensure_contiguous=True)
    return np.allclose(qiskit_u, cirq_u)

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
Module defining AnalogHamiltonianProgram Class

"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from qbraid.programs.program import QuantumProgram

if TYPE_CHECKING:
    import qbraid.runtime


class AnalogHamiltonianProgram(QuantumProgram, ABC):
    """Abstract class for qbraid program wrapper objects."""

    @property
    def hamiltonian(self) -> dict:
        """Return the Hamiltonian of the program."""
        return self.to_dict()["hamiltonian"]

    @property
    def register(self) -> dict:
        """AtomArrangement: The initial atom arrangement for the simulation."""
        return self.to_dict()["register"]

    @property
    def num_atoms(self) -> int:
        """Return the number of atoms in the program."""
        return len(self.register["sites"])

    @property
    def num_qubits(self) -> int:
        """Number of qubits needed by a quantum device to execute this program."""
        return self.num_atoms

    def transform(self, device: qbraid.runtime.QuantumDevice) -> None:
        """Transform program to according to device target profile."""
        return None

    @abstractmethod
    def to_dict(self) -> dict:
        """Return the dictionary representation of the program."""

    def serialize(self) -> dict[str, str]:
        """Return the program in a format suitable for submission to the qBraid API."""
        return {"ahs": json.dumps(self, cls=AHSEncoder)}

    def __eq__(self, other: Any) -> bool:
        """Check if two programs are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.to_dict() == other.to_dict()


class AHSEncoder(json.JSONEncoder):
    """Class for encoding AnalogHamiltonianProgram objects to dictionaries.

    Example:

    .. code-block:: python

        >>> import json
        >>> from qbraid.programs.ahs import AHSEncoder
        >>> json_str = json.dumps(ahs_program, cls=AHSEncoder)

    """

    def default(self, o: Any) -> Any:
        if isinstance(o, AnalogHamiltonianProgram):
            return o.to_dict()
        return super().default(o)

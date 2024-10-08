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
Module defining AnalogHamiltonianProgram Class

"""
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

    def transform(self, device: "qbraid.runtime.QuantumDevice") -> None:
        """Transform program to according to device target profile."""
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict:
        """Return the dictionary representation of the program."""

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

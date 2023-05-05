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
Module defining PyQuilProgramWrapper Class

"""
from pyquil import Program

from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class PyQuilProgramWrapper(QuantumProgramWrapper):
    """Wrapper class for pyQuil ``Program`` objects."""

    def __init__(self, program: Program):
        """Create a PyQuilProgramWrapper

        Args:
            program: the program object to be wrapped

        """
        super().__init__(program)

        self._qubits = program.get_qubits()
        self._num_qubits = len(self.qubits)
        self._depth = len(program)
        self._package = "pyquil"
        self._program_type = "Program"

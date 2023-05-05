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
Module containing pyQuil tools

"""
import numpy as np
from pyquil import Program
from pyquil.simulation.tools import program_unitary


def _unitary_from_pyquil(program: Program) -> np.ndarray:
    """Return the unitary of a pyQuil program."""
    n_qubits = len(program.get_qubits())
    return program_unitary(program, n_qubits=n_qubits)

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

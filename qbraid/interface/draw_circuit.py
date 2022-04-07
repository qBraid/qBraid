"""Module for drawing quantum circuit diagrams"""

from qbraid._typing import QPROGRAM
from qbraid.exceptions import ProgramTypeError


def draw(program: QPROGRAM) -> None:
    """Draws circuit diagram."""

    try:
        package = program.__module__
    except AttributeError as err:
        raise ProgramTypeError(program) from err

    if "qiskit" in package:
        program.draw()

    elif "pennylane" in package:
        print(program.draw())

    elif "braket" in package or "cirq" in package or "pyquil" in package:
        print(program)

    else:
        raise ProgramTypeError(program)

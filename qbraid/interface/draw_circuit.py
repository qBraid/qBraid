"""Module for drawing quantum circuit diagrams"""

from typing import TYPE_CHECKING

from qbraid.exceptions import ProgramTypeError

if TYPE_CHECKING:
    import qbraid


def draw(program: "qbraid.QPROGRAM") -> None:
    """Draws circuit diagram.

    Args:
        :data:`~.qbraid.QPROGRAM`: Supported quantum program

    Raises:
        ProgramTypeError: If quantum program is not of a supported type
    """

    try:
        package = program.__module__
    except AttributeError as err:
        raise ProgramTypeError(program) from err

    if "qiskit" in package or "pennylane" in package:
        print(program.draw())

    elif "braket" in package or "cirq" in package or "pyquil" in package:
        print(program)

    else:
        raise ProgramTypeError(program)

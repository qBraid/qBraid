"""Module for creating bell circuits for testing"""

from typing import Any, Callable

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import QbraidError, UnsupportedProgramError


def bell(package: str) -> QPROGRAM:
    """Creates bell circuit in given package

    Args:
        package: Target package with which to create quantum program

    Raises:
        UnsupportedProgramError: If the input quantum program is not supported.

    Returns:
        numpy.ndarray: Matrix representation of the input quantum program.
    """
    bell_function: Callable[[Any], QPROGRAM]

    # pylint: disable=import-outside-toplevel

    if package == "braket":
        from qbraid.interface.qbraid_braket.circuits import braket_bell

        bell_function = braket_bell
    elif package == "cirq":
        from qbraid.interface.qbraid_cirq.circuits import cirq_bell

        bell_function = cirq_bell
    elif package == "pennylane":
        from qbraid.interface.qbraid_pennylane.tapes import pennylane_bell

        bell_function = pennylane_bell
    elif package == "pyquil":
        from qbraid.interface.qbraid_pyquil.programs import pyquil_bell

        bell_function = pyquil_bell
    elif package == "qiskit":
        from qbraid.interface.qbraid_qiskit.circuits import qiskit_bell

        bell_function = qiskit_bell
    else:
        raise UnsupportedProgramError(
            f"Frontend module {package} is not supported.\n\n"
            f"Frontend modules supported by qBraid are \n{list(SUPPORTED_PROGRAM_TYPES.keys())}"
        )

    try:
        circuit = bell_function()
    except Exception as err:
        raise QbraidError(
            f"Bell circuit could not be created for frontend module {package}."
        ) from err

    return circuit

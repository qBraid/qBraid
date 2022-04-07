"""Module containing quantum programs used for testing"""

from typing import Any, Callable, Dict

import numpy as np

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import PackageValueError

QROGRAM_MAP = Dict[str, Callable[[Any], QPROGRAM]]

# pylint: disable=import-outside-toplevel


def bell_circuits() -> QROGRAM_MAP:
    """Returns bell circuit/program in each supported package."""
    from qbraid.interface.qbraid_braket.circuits import braket_bell
    from qbraid.interface.qbraid_cirq.circuits import cirq_bell
    from qbraid.interface.qbraid_pennylane.tapes import pennylane_bell
    from qbraid.interface.qbraid_pyquil.programs import pyquil_bell
    from qbraid.interface.qbraid_qiskit.circuits import qiskit_bell

    return {
        "braket": braket_bell,
        "cirq": cirq_bell,
        "pennylane": pennylane_bell,
        "pyquil": pyquil_bell,
        "qiskit": qiskit_bell,
    }


def shared15_circuits() -> QROGRAM_MAP:
    """Returns shared gates circuit/program in each supported package."""
    from qbraid.interface.qbraid_braket.circuits import braket_shared15
    from qbraid.interface.qbraid_cirq.circuits import cirq_shared15
    from qbraid.interface.qbraid_qiskit.circuits import qiskit_shared15

    return {"braket": braket_shared15, "cirq": cirq_shared15, "qiskit": qiskit_shared15}


def random_circuit(package: str, **kwargs) -> QPROGRAM:
    """Generate random circuit of arbitrary size and form.

    Args:
        package (str): qbraid supported software package
        num_qubits (optional, int): number of quantum wires. If not provided,
            set randomly in range [2,4].
        depth (optional, int): layers of operations (i.e. critical path length)
            If not provided, set randomly in range [2,4].

    Raises:
        PackageValueError: if ``package`` is not supported
        QbraidError: when invalid random circuit options given

    Returns:
        :ref:`QPROGRAM<data_types>`: randomly generated quantum circuit/program

    """
    if package not in SUPPORTED_PROGRAM_TYPES:
        raise PackageValueError(package)
    num_qubits = np.random.randint(1, 4) if "num_qubits" not in kwargs else kwargs.pop("num_qubits")
    depth = np.random.randint(1, 4) if "depth" not in kwargs else kwargs.pop("depth")
    if package == "qiskit":
        from qbraid.interface.qbraid_qiskit.circuits import _qiskit_random

        rand_circuit = _qiskit_random(num_qubits, depth, **kwargs)
    else:
        from qbraid.interface.qbraid_cirq.circuits import _cirq_random

        rand_circuit = _cirq_random(num_qubits, depth, **kwargs)

        if package != "cirq":
            from qbraid import circuit_wrapper

            rand_circuit = circuit_wrapper(rand_circuit).transpile(package)

    return rand_circuit

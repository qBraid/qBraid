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
Module containing quantum programs used for testing

"""

from typing import Any, Callable, Dict, Tuple

import numpy as np

from qbraid import circuit_wrapper
from qbraid._qprogram import QPROGRAM

from .braket.circuits import braket_bell, braket_shared15
from .cirq.circuits import cirq_bell, cirq_shared15
from .pyquil.programs import pyquil_bell, pyquil_shared15
from .pytket.circuits import pytket_bell, pytket_shared15
from .qasm2.circuits import qasm2_bell, qasm2_cirq_shared15
from .qasm3.circuits import qasm3_bell, qasm3_shared15
from .qiskit.circuits import qiskit_bell, qiskit_shared15

QROGRAM_TEST_TYPE = Tuple[Dict[str, Callable[[Any], QPROGRAM]], np.ndarray]


def bell_data() -> QROGRAM_TEST_TYPE:
    """Returns bell circuit/program in each supported package."""

    unitary = circuit_wrapper(cirq_bell()).unitary()

    circuits = {
        "braket": braket_bell,
        "cirq": cirq_bell,
        "pyquil": pyquil_bell,
        "qiskit": qiskit_bell,
        "pytket": pytket_bell,
        "qasm2": qasm2_bell,
        "qasm3": qasm3_bell,
    }

    return circuits, unitary


def shared15_data() -> QROGRAM_TEST_TYPE:
    """Returns shared gates circuit/program in each supported package."""

    unitary = circuit_wrapper(cirq_shared15()).unitary()

    circuits = {
        "braket": braket_shared15,
        "cirq": cirq_shared15,
        "pyquil": pyquil_shared15,
        "qiskit": qiskit_shared15,
        "pytket": pytket_shared15,
        "qasm2": qasm2_cirq_shared15,
        "qasm3": qasm3_shared15,
    }

    return circuits, unitary

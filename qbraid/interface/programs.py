# Copyright 2023 qBraid
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
Module containing quantum programs used for testing

"""
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

import numpy as np

from qbraid._qprogram import QPROGRAM, QPROGRAM_LIBS
from qbraid.exceptions import PackageValueError

from .calculate_unitary import to_unitary

QROGRAM_TEST_TYPE = Tuple[Dict[str, Callable[[Any], QPROGRAM]], np.ndarray]

if TYPE_CHECKING:
    import qbraid

# pylint: disable=import-outside-toplevel


def bell_data() -> QROGRAM_TEST_TYPE:
    """Returns bell circuit/program in each supported package."""
    from qbraid.interface.qbraid_braket.circuits import braket_bell
    from qbraid.interface.qbraid_cirq.circuits import cirq_bell
    from qbraid.interface.qbraid_pyquil.programs import pyquil_bell
    from qbraid.interface.qbraid_pytket.circuits import pytket_bell
    from qbraid.interface.qbraid_qiskit.circuits import qiskit_bell

    unitary = to_unitary(cirq_bell())

    circuits = {
        "braket": braket_bell,
        "cirq": cirq_bell,
        "pyquil": pyquil_bell,
        "qiskit": qiskit_bell,
        "pytket": pytket_bell,
    }

    return circuits, unitary


def shared15_data() -> QROGRAM_TEST_TYPE:
    """Returns shared gates circuit/program in each supported package."""
    from qbraid.interface.qbraid_braket.circuits import braket_shared15
    from qbraid.interface.qbraid_cirq.circuits import cirq_shared15
    from qbraid.interface.qbraid_pytket.circuits import pytket_shared15
    from qbraid.interface.qbraid_qiskit.circuits import qiskit_shared15

    unitary = to_unitary(cirq_shared15())

    circuits = {
        "braket": braket_shared15,
        "cirq": cirq_shared15,
        "qiskit": qiskit_shared15,
        "pytket": pytket_shared15,
    }

    return circuits, unitary


def random_circuit(
    package: str, num_qubits: Optional[int] = None, depth: Optional[int] = None, **kwargs
) -> "qbraid.QPROGRAM":
    """Generate random circuit of arbitrary size and form.

    Args:
        package: qBraid supported software package
        num_qubits: Number of quantum wires. If not provided, set randomly in range [2,4].
        depth: Layers of operations (i.e. critical path length)
            If not provided, set randomly in range [2,4].

    Raises:
        PackageValueError: if ``package`` is not supported
        QbraidError: when invalid random circuit options given

    Returns:
        :data:`~qbraid.QPROGRAM`: randomly generated quantum circuit/program

    """
    # todo: custom random gate
    if package not in QPROGRAM_LIBS:
        raise PackageValueError(package)
    num_qubits = np.random.randint(1, 4) if num_qubits is None else num_qubits
    depth = np.random.randint(1, 4) if depth is None else depth
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

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
Module for transforming Qiskit circuits.

"""
import logging
from typing import TYPE_CHECKING

from qiskit import transpile

from qbraid.programs.libs.qiskit import QiskitCircuit

if TYPE_CHECKING:
    import qiskit

    import qbraid.runtime.qiskit


logger = logging.getLogger(__name__)


def transform(
    circuit: "qiskit.QuantumCircuit", device: "qbraid.runtime.qiskit.QiskitBackend"
) -> "qiskit.QuantumCircuit":
    """Transpile a circuit for the device."""
    if device.device_type.name == "LOCAL_SIMULATOR":
        program = QiskitCircuit(circuit)
        try:
            program.remove_idle_qubits()
            circuit = program.program
        except ValueError:
            logger.debug("Failed to remove idle qubits for device %s", device.id)

    return transpile(circuit, backend=device._backend)

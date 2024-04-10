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
Module for converting Braket circuits to/from Cirq

"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import braket.circuits
    import cirq


def braket_to_cirq(circuit: "braket.circuits.Circuit") -> "cirq.Circuit":
    """Returns a Cirq circuit equivalent to the input Braket circuit.

    Note: The returned Cirq circuit acts on cirq.LineQubit's with indices equal
    to the qubit indices of the Braket circuit.

    Args:
        circuit: Braket circuit to convert to a Cirq circuit.
    """
    # pylint: disable-next=import-outside-toplevel
    from .cirq_from_braket import _braket_to_cirq

    return _braket_to_cirq(circuit)


def cirq_to_braket(circuit: "cirq.Circuit") -> "braket.circuits.Circuit":
    """Returns a Braket circuit equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a Braket circuit.

    Returns:
        Braket circuit equivalent to the input Cirq circuit.
    """
    # pylint: disable-next=import-outside-toplevel
    from .cirq_to_braket import _cirq_to_braket

    return _cirq_to_braket(circuit)

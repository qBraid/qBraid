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
Unit tests for submissions to AWS SV1, DM1, TN1 via qBraid native runtime.

"""

from qbraid.runtime.native.provider import _braket_to_json


def test_braket_circuit_to_json(braket_circuit, qasm3_circuit):
    """Test conversion of Braket circuit to JSON."""
    qasm_json = _braket_to_json(braket_circuit)
    assert qasm_json == {"openQasm": qasm3_circuit}

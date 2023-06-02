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
Unit tests for working with IBM provider

"""
import os

import pytest
from qiskit_ibm_provider import IBMProvider

from qbraid.devices.ibm.provider import ibm_least_busy_qpu, ibm_provider, ibm_to_qbraid_id

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"

backend_id_data = [
    ("ibm_nairobi", "ibm_q_nairobi"),
    ("ibmq_belem", "ibm_q_belem"),
    ("simulator_extended_stabilizer", "ibm_q_simulator_extended_stabilizer"),
]


@pytest.mark.parametrize("data", backend_id_data)
def test_get_qbraid_id(data):
    """Test converting backend name to qbraid_id."""
    original, expected = data
    result = ibm_to_qbraid_id(original)
    assert result == expected


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_ibm_provider():
    """Test getting IBMQ provider using qiskit_ibm_provider package."""
    ibmq_token = os.getenv("QISKIT_IBM_TOKEN", None)
    provider = ibm_provider(token=ibmq_token)
    assert isinstance(provider, IBMProvider)


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_ibm_least_busy():
    """Test returning qbraid ID of least busy IBMQ QPU."""
    qbraid_id = ibm_least_busy_qpu()
    assert qbraid_id[:6] == "ibm_q_"

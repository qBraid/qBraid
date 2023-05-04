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
Unit tests for working with IBM provider

"""
import os

import pytest
from qiskit_ibm_provider import IBMProvider

from qbraid.devices.ibm.provider import ibm_least_busy_qpu, ibm_provider, ibm_to_qbraid_id

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


def test_ibm_provider():
    """Test getting IBMQ provider using qiskit_ibm_provider package."""
    ibmq_token = os.getenv("QISKIT_IBM_TOKEN", None)
    provider = ibm_provider(token=ibmq_token)
    assert isinstance(provider, IBMProvider)


def test_ibm_least_busy():
    """Test returning qbraid ID of least busy IBMQ QPU."""
    qbraid_id = ibm_least_busy_qpu()
    assert qbraid_id[:6] == "ibm_q_"

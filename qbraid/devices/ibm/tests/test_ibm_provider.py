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

from qbraid.devices.ibm.provider import ibm_least_busy_qpu, ibm_provider

ibmq_token = os.getenv("QISKIT_IBM_TOKEN")


def test_ibm_provider():
    """Test getting IBMQ provider using qiskit_ibm_provider package."""
    from qiskit_ibm_provider import IBMProvider

    provider = ibm_provider(token=ibmq_token)
    assert isinstance(provider, IBMProvider)


def test_ibmq_least_busy():
    """Test returning qbraid ID of least busy IBMQ QPU."""
    qbraid_id = ibm_least_busy_qpu()
    assert qbraid_id[:6] == "ibm_q_"

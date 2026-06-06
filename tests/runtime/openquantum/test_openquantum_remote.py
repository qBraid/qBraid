# Copyright 2025 qBraid
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
Unit tests for OpenQuantum runtime (remote)
"""
import os

import pytest
from qbraid_core.exceptions import RequestsApiError

from qbraid._logging import logger
from qbraid.runtime import (
    GateModelResultData,
    JobStateError,
    OpenQuantumDevice,
    OpenQuantumProvider,
    Result,
)


@pytest.mark.remote
def test_openquantum_remote_job():
    """Test running a simple remote job on OpenQuantum."""
    client_id = os.getenv("OPENQUANTUM_CLIENT_ID")
    client_secret = os.getenv("OPENQUANTUM_CLIENT_SECRET")

    if not client_id or not client_secret:
        pytest.skip("OPENQUANTUM_CLIENT_ID and OPENQUANTUM_CLIENT_SECRET are not set.")

    try:
        provider = OpenQuantumProvider(client_id=client_id, client_secret=client_secret)
        device = provider.get_device("oq-sim")
    except Exception as e:  # pylint: disable=broad-exception-caught
        pytest.skip(f"Could not initialize provider or get device: {e}")

    assert isinstance(device, OpenQuantumDevice)

    qasm_ghz = """
    OPENQASM 3.0;
    qubit[3] q;
    bit[3] c;
    h q[0];
    cx q[0], q[1];
    cx q[0], q[2];
    c = measure q;
    """

    job = device.run(qasm_ghz, name="qBraid SDK Remote Test", shots=100, subcategory="oth:oth")

    try:
        job.wait_for_final_state(timeout=300)
    except TimeoutError as err:
        logger.error(err)
        try:
            job.cancel()
        except (RequestsApiError, JobStateError) as cancel_err:
            logger.error(cancel_err)
        pytest.skip(reason="Job did not complete within the timeout")

    result = job.result()
    assert isinstance(result, Result)

    result_data = result.data
    assert isinstance(result_data, GateModelResultData)

    counts = result_data.get_counts()
    assert "000" in counts
    assert "111" in counts
    assert sum(counts.values()) == 100

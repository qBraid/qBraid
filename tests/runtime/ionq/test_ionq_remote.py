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
Unit tests for IonQ runtime (remote)

"""

import os
from typing import TYPE_CHECKING

import pytest
from qbraid_core.exceptions import RequestsApiError

from qbraid._logging import logger
from qbraid.runtime import GateModelResultData, IonQDevice, IonQProvider, JobStateError, Result

if TYPE_CHECKING:
    import cirq as cirq_module
    import qiskit as qiskit_module


@pytest.mark.remote
def test_ionq_multicircuit_job():
    """Test running multiple circuits in a single job."""
    cirq: cirq_module = pytest.importorskip("cirq")
    qiskit: qiskit_module = pytest.importorskip("qiskit")

    api_key = os.getenv("IONQ_API_KEY")

    if not api_key:
        pytest.skip("IONQ_API_KEY is not set")

    provider = IonQProvider(api_key=api_key)
    device = provider.get_device("simulator")

    qiskit_ghz = qiskit.QuantumCircuit(3)
    qiskit_ghz.h(0)
    qiskit_ghz.cx(0, 1)
    qiskit_ghz.cx(0, 2)

    # Deliberately not a Bell state: {"00", "11"} is symmetric under bit reversal and
    # would stay green if the IonQ bit order regressed. X on q0 alone is asymmetric,
    # so the order and the batch widening are both pinned. The identity keeps q1 in
    # the circuit so it stays two qubits wide.
    cirq_circuit = cirq.Circuit()
    q0, q1 = cirq.LineQubit.range(2)
    cirq_circuit.append(cirq.X(q0))
    cirq_circuit.append(cirq.I(q1))

    device = provider.get_device("simulator")

    assert isinstance(device, IonQDevice)

    job = device.run([qiskit_ghz, cirq_circuit], name="qBraid Integration Test", shots=1000)

    try:
        job.wait_for_final_state(timeout=60)
    except TimeoutError as err:
        logger.error(err)

        try:
            job.cancel()
        except (RequestsApiError, JobStateError) as err:
            logger.error(err)

        pytest.skip(reason="Job did not complete within the timeout")

    result = job.result()

    assert isinstance(result, Result)

    result_data = result.data

    assert isinstance(result_data, GateModelResultData)

    counts = result_data.get_counts()

    # qubit 0 is leftmost and the 2-qubit result widens to the right, so X on q0
    # of a 2-qubit circuit reads "100" once padded to the batch width.
    assert counts == [{"000": 500, "111": 500}, {"100": 1000}]

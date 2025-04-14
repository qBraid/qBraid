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

    cirq_bell = cirq.Circuit()
    q0, q1 = cirq.LineQubit.range(2)
    cirq_bell.append(cirq.H(q0))
    cirq_bell.append(cirq.CNOT(q0, q1))

    device = provider.get_device("simulator")

    assert isinstance(device, IonQDevice)

    job = device.run([qiskit_ghz, cirq_bell], name="qBraid Integration Test", shots=1000)

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

    assert counts == [{"000": 500, "111": 500}, {"000": 500, "011": 500}]

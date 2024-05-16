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
Unit tests for QiskitProvider class

"""
import time
from typing import Union

import pytest
from qiskit import QuantumCircuit
from qiskit_aer import AerJob
from qiskit_ibm_runtime import RuntimeJob

from qbraid.runtime import JobStateError

from .fixtures import fake_ibm_devices, test_circuits

circuits_qiskit_run = test_circuits


@pytest.mark.parametrize("device", fake_ibm_devices())
def test_retrieving_ibm_job(device):
    """Test retrieving a previously submitted IBM job."""
    circuit = QuantumCircuit(1, 1)
    circuit.h(0)
    circuit.measure(0, 0)
    qbraid_job = device.run(circuit, shots=1)
    ibm_job = qbraid_job._job
    assert isinstance(ibm_job, Union[RuntimeJob, AerJob])


@pytest.mark.parametrize("device", fake_ibm_devices())
def test_cancel_completed_batch_error(device):
    """Test that cancelling a batch job that has already reached its
    final state raises an error."""
    job = device.run(circuits_qiskit_run, shots=10)

    timeout = 30
    check_every = 2
    elapsed_time = 0

    while elapsed_time < timeout:
        if job.is_terminal_state():
            break

        time.sleep(check_every)
        elapsed_time += check_every

    if elapsed_time >= timeout:
        try:
            job.cancel()
        except JobStateError:
            pass

    with pytest.raises(JobStateError):
        job.cancel()

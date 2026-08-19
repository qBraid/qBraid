# Copyright 2026 qBraid
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
Remote integration tests for the QPerfect (MIMIQ) provider, device, and job classes.

These submit real jobs to the MIMIQ cloud emulator and verify end-to-end result flow.
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("mimiqcircuits")
pytest.importorskip("mimiq_qiskit")

# pylint: disable=wrong-import-position
from qiskit import QuantumCircuit  # noqa: E402

from qbraid.runtime.enums import DeviceStatus, JobStatus  # noqa: E402
from qbraid.runtime.qperfect import QPerfectDevice, QPerfectJob, QPerfectProvider  # noqa: E402
from qbraid.runtime.result import Result  # noqa: E402

DEVICE_ID = "mimiq-emulator"
SHOTS = 100


def _get_provider() -> QPerfectProvider:
    """Return a provider built from the environment, skipping if the token is unset."""
    if not os.getenv("QPERFECT_API_TOKEN"):
        pytest.skip("QPERFECT_API_TOKEN is not set")
    return QPerfectProvider()


def _bell() -> QuantumCircuit:
    """A two-qubit Bell circuit with both qubits measured."""
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    return circuit


@pytest.mark.remote
def test_provider_get_devices():
    """Provider lists the single MIMIQ cloud emulator."""
    devices = _get_provider().get_devices()
    assert len(devices) == 1
    assert all(isinstance(device, QPerfectDevice) for device in devices)


@pytest.mark.remote
def test_device_status_online():
    """The emulator reports ONLINE once the connection authenticates."""
    device = _get_provider().get_device(DEVICE_ID)
    assert device.status() == DeviceStatus.ONLINE


@pytest.mark.remote
def test_single_circuit_run():
    """A Bell circuit round-trips through transpilation, submission, and result retrieval."""
    device = _get_provider().get_device(DEVICE_ID)
    job = device.run(_bell(), shots=SHOTS)
    assert isinstance(job, QPerfectJob)

    result = job.result()
    assert isinstance(result, Result)
    assert result.success
    assert job.status() == JobStatus.COMPLETED

    counts = result.data.get_counts()
    assert sum(counts.values()) == SHOTS
    assert set(counts) <= {"00", "11"}


@pytest.mark.remote
@pytest.mark.parametrize("qubit, expected", [(0, "001"), (2, "100")])
def test_result_bitstring_endianness(qubit, expected):
    """Counts follow qBraid's little-endian convention (qubit 0 rightmost).

    ``BitString.to01`` orders qubit 0 first, so the job reverses each key. Flipping a single
    qubit of three is what distinguishes a correct reversal from a no-op.
    """
    device = _get_provider().get_device(DEVICE_ID)
    circuit = QuantumCircuit(3, 3)
    circuit.x(qubit)
    circuit.measure([0, 1, 2], [0, 1, 2])

    counts = device.run(circuit, shots=SHOTS).result().data.get_counts()
    assert counts == {expected: SHOTS}


@pytest.mark.remote
def test_batch_run_returns_counts_per_circuit():
    """A batch executes as one job, with results ordered by submission."""
    device = _get_provider().get_device(DEVICE_ID)
    flip = QuantumCircuit(1, 1)
    flip.x(0)
    flip.measure(0, 0)

    job = device.run([_bell(), flip], shots=SHOTS, algorithm="statevector")
    counts = job.result().data.get_counts()

    assert isinstance(counts, list)
    assert len(counts) == 2
    assert set(counts[0]) <= {"00", "11"}

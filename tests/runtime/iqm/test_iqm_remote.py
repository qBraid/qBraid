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
Remote tests for the IQM runtime, exercised against IQM Resonance.

Set ``IQM_TOKEN`` to run these. Submissions target the ``:mock`` backend, IQM's
simulated twin of a QPU, so the suite does not consume QPU time.

"""
from __future__ import annotations

import os

import pytest

from qbraid.runtime import DeviceStatus, JobStatus
from qbraid.runtime.iqm import IQMDevice, IQMProvider

pytestmark = pytest.mark.remote

MOCK_DEVICE_ID = "garnet:mock"
# Star architecture: a computational resonator, reached through MOVE.
STAR_DEVICE_ID = "sirius:mock"


def provider_or_skip() -> IQMProvider:
    """Return a provider, skipping when no usable credential is configured.

    ``IQMClient`` never validates the token locally, so an expired one only surfaces
    on the first request. Treat that as "no usable credential" rather than a failure,
    so a rotated secret does not turn the daily run red.
    """
    if not os.getenv("IQM_TOKEN"):
        pytest.skip("Missing IQM_TOKEN")

    # pylint: disable-next=import-outside-toplevel
    from iqm.iqm_client import AuthenticationError, ForbiddenError, UnauthorizedError

    provider = IQMProvider()
    try:
        provider.session.list_quantum_computers()
    except (AuthenticationError, ForbiddenError, UnauthorizedError) as err:
        pytest.skip(f"IQM rejected IQM_TOKEN; it has most likely expired: {err}")
    return provider


@pytest.fixture(scope="module")
def provider() -> IQMProvider:
    """Return an authenticated IQM provider."""
    return provider_or_skip()


def test_get_devices_returns_configured_quantum_computers(provider):
    """Every alias the account can see becomes a device."""
    devices = provider.get_devices()
    assert devices
    assert all(isinstance(device, IQMDevice) for device in devices)
    assert all(device.profile.num_qubits > 0 for device in devices)
    # IQM exposes a simulated twin of each QPU under a ":mock" alias.
    assert {d.id.endswith(":mock") for d in devices} == {d.profile.simulator for d in devices}


def test_get_device_is_targeted(provider):
    """A device is fetched by alias without building the others."""
    device = provider.get_device(MOCK_DEVICE_ID)
    assert device.id == MOCK_DEVICE_ID
    assert device.status() == DeviceStatus.ONLINE


def test_unknown_device_names_the_alternatives(provider):
    """An unknown alias reports what is available."""
    from qbraid.runtime.exceptions import ResourceNotFoundError  # pylint: disable=C0415

    with pytest.raises(ResourceNotFoundError, match="Available devices"):
        provider.get_device("not-a-real-device")


def test_qiskit_circuit_round_trip(provider):
    """A Qiskit Bell circuit runs and returns counts over both basis states."""
    qiskit = pytest.importorskip("qiskit")

    circuit = qiskit.QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    device = provider.get_device(MOCK_DEVICE_ID)
    job = device.run(circuit, shots=100)
    job.wait_for_final_state(timeout=300)
    assert job.status() == JobStatus.COMPLETED

    counts = job.result().data.get_counts()
    assert sum(counts.values()) == 100
    assert all(len(bitstring) == 2 for bitstring in counts)


def test_cirq_circuit_round_trip(provider):
    """A Cirq circuit reaches IQM through the transpiler, with no Qiskit required."""
    cirq = pytest.importorskip("cirq")

    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit([cirq.X(qubits[0]), cirq.measure(*qubits, key="m")])

    device = provider.get_device(MOCK_DEVICE_ID)
    job = device.run(circuit, shots=50)
    job.wait_for_final_state(timeout=300)
    assert job.status() == JobStatus.COMPLETED

    counts = job.result().data.get_counts()
    assert sum(counts.values()) == 50


def test_star_architecture_round_trip(provider):
    """A Star-architecture device routes through its resonator and returns counts.

    Regression: routed circuits were serialized against the static architecture's
    qubit list, which is neither the backend's index space nor inclusive of the
    resonator, so every Sirius submission failed with "MOVE instructions are only
    allowed between qubit and resonator". Placement then remapped the resonator to
    a qubit. Crystal-architecture devices cannot catch either.
    """
    qiskit = pytest.importorskip("qiskit")

    device = provider.get_device(STAR_DEVICE_ID)
    assert device.profile.get("computational_resonators")

    circuit = qiskit.QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    job = device.run(circuit, shots=50)
    job.wait_for_final_state(timeout=300)
    assert job.status() == JobStatus.COMPLETED
    assert sum(job.result().data.get_counts().values()) == 50


def test_star_architecture_keeps_move_on_the_resonator(provider):
    """MOVE loci must name a resonator; remapping one makes the instruction invalid."""
    qiskit = pytest.importorskip("qiskit")

    device = provider.get_device(STAR_DEVICE_ID)
    resonators = set(device.profile.get("computational_resonators") or ())

    circuit = qiskit.QuantumCircuit(3, 3)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure(range(3), range(3))

    prepared = device.apply_runtime_profile(circuit)
    placed = device._place(prepared)
    moves = [op.locus for op in placed.instructions if op.name == "move"]

    assert moves, "expected the Star architecture to route through its resonator"
    assert all(len(set(locus) & resonators) == 1 for locus in moves)
    assert {q for op in placed.instructions for q in op.locus} <= device.components


def test_device_width_reflects_the_calibration_set(provider):
    """A device is as wide as its calibration set, not as wide as the chip."""
    device = provider.get_device(STAR_DEVICE_ID)
    chip = device.profile.get("chip_qubits")

    assert device.num_qubits == len(device.qubits)
    assert set(device.qubits) <= set(chip)

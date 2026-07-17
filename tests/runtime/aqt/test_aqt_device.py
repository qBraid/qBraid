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
Unit tests for the ``AQTDevice`` status mapping, job submission body, and the ``run`` pipeline.

The ``device`` / ``mock_session`` / ``aqt_circuit`` fixtures come from ``conftest.py``; the arnica
HTTP session is mocked, so no network access occurs.
"""

from __future__ import annotations

import pytest
from qiskit import QuantumCircuit as QiskitCircuit

from qbraid.runtime.aqt import AQTJob
from qbraid.runtime.enums import DeviceStatus

# ---------------------------------------------------------------------------
# device: status
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status,expected",
    [
        ("online", DeviceStatus.ONLINE),
        ("offline", DeviceStatus.OFFLINE),
        ("maintenance", DeviceStatus.UNAVAILABLE),
        ("unavailable", DeviceStatus.UNAVAILABLE),
    ],
)
def test_device_status_mapping(device, mock_session, status, expected):
    """The arnica resource status is mapped to the qBraid ``DeviceStatus``."""
    mock_session.get_resource.return_value = {"status": status}
    assert device.status() == expected


def test_device_status_unknown_raises(device, mock_session):
    """An unrecognized status raises ``ValueError``."""
    mock_session.get_resource.return_value = {"status": "banana"}
    with pytest.raises(ValueError):
        device.status()


def test_device_str(device):
    """``str(device)`` renders the device id."""
    assert str(device) == "AQTDevice('default/sim1')"


# ---------------------------------------------------------------------------
# device: submit
# ---------------------------------------------------------------------------


def test_device_submit_single_body_shape(device, mock_session, aqt_circuit):
    """A single native circuit is submitted with ``repetitions=shots`` and ``name`` as the label."""
    circuit = aqt_circuit(number_of_qubits=2)
    job = device.submit(circuit, shots=250, name="demo")

    assert isinstance(job, AQTJob)
    assert job.id == "job-1"

    mock_session.submit_job.assert_called_once()
    ws, res, body = mock_session.submit_job.call_args.args
    assert (ws, res) == ("default", "sim1")
    assert body["job_type"] == "quantum_circuit"
    assert body["label"] == "demo"

    circuits = body["payload"]["circuits"]
    assert len(circuits) == 1
    assert circuits[0]["repetitions"] == 250
    assert circuits[0]["number_of_qubits"] == 2


def test_device_submit_default_label(device, mock_session, aqt_circuit):
    """When ``name`` is omitted, the job label defaults to ``"qbraid"``."""
    device.submit(aqt_circuit(), shots=10)
    _ws, _res, body = mock_session.submit_job.call_args.args
    assert body["label"] == "qbraid"


def test_device_submit_batch(device, mock_session, aqt_circuit):
    """A list of circuits is submitted as a single batch with per-circuit ``repetitions=shots``."""
    circuits = [aqt_circuit(2), aqt_circuit(2)]
    device.submit(circuits, shots=64)

    _ws, _res, body = mock_session.submit_job.call_args.args
    payload_circuits = body["payload"]["circuits"]
    assert len(payload_circuits) == 2
    assert all(c["repetitions"] == 64 for c in payload_circuits)


def test_device_submit_missing_job_id_raises(device, mock_session, aqt_circuit):
    """A submission response without a ``job_id`` raises ``ValueError``."""
    mock_session.submit_job.return_value = {"job": {}}
    with pytest.raises(ValueError):
        device.submit(aqt_circuit())


def test_device_run_end_to_end(device, mock_session):
    """``run`` transpiles a qiskit circuit through the ``qiskit -> aqt`` edge, then submits it."""
    # ``run`` -> validate -> status() -> get_resource must report online.
    mock_session.get_resource.return_value = {"status": "online"}

    qc = QiskitCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()

    job = device.run(qc, shots=250)
    assert isinstance(job, AQTJob)

    _ws, _res, body = mock_session.submit_job.call_args.args
    circuit = body["payload"]["circuits"][0]
    assert circuit["repetitions"] == 250
    assert circuit["number_of_qubits"] == 2
    assert circuit["quantum_circuit"][-1]["operation"] == "MEASURE"

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
from aqt_connector.models.arnica.response_bodies.jobs import SubmitJobResponse
from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails
from pydantic import ValidationError
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
def test_device_status_mapping(device, mock_session, simulator_resource, status, expected):
    """Every arnica ``ResourceStatus`` maps to the corresponding qBraid ``DeviceStatus``."""
    mock_session.get_resource.return_value = ResourceDetails.model_validate(
        {**simulator_resource, "status": status}
    )
    assert device.status() == expected


def test_device_status_unknown_rejected_at_the_source(simulator_resource):
    """A status outside arnica's enum fails validation instead of reaching the status map.

    The device never sees a bogus status: ``AQTSession.get_resource`` validates the payload, so
    an unmapped value surfaces as a ``ValidationError`` naming the offending field rather than
    a ``DeviceStatus`` guess made downstream.
    """
    with pytest.raises(ValidationError, match="status"):
        ResourceDetails.model_validate({**simulator_resource, "status": "banana"})


def test_device_status_missing_field_rejected(simulator_resource):
    """A resource payload missing ``available_qubits`` fails loudly rather than defaulting.

    Regression guard: the profile builder previously used ``resource.get("available_qubits")``,
    which would quietly produce a device advertising ``num_qubits=None``.
    """
    del simulator_resource["available_qubits"]
    with pytest.raises(ValidationError, match="available_qubits"):
        ResourceDetails.model_validate(simulator_resource)


def test_device_str(device):
    """``str(device)`` renders the device id."""
    assert str(device) == "AQTDevice('aqt_simulators/simulator_no_noise')"


# ---------------------------------------------------------------------------
# device: submit
# ---------------------------------------------------------------------------


def test_device_submit_single_body_shape(device, mock_session, aqt_circuit):
    """A single native circuit is submitted with ``repetitions=shots`` and ``name`` as the label."""
    circuit = aqt_circuit(number_of_qubits=2)
    job = device.submit(circuit, shots=250, name="demo")

    assert isinstance(job, AQTJob)
    assert job.id == "6f1b6a1e-2f1e-4c3a-9d5b-1f0a2b3c4d5e"

    mock_session.submit_job.assert_called_once()
    ws, res, body = mock_session.submit_job.call_args.args
    assert (ws, res) == ("aqt_simulators", "simulator_no_noise")
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


def test_submit_response_missing_job_id_rejected():
    """A submission response without a ``job_id`` fails validation in the session.

    Regression guard: ``response.get("job", {}).get("job_id")`` returned ``None`` here, so the
    error surfaced (if at all) as an ``AQTJob`` holding the string ``"None"``.
    """
    with pytest.raises(ValidationError, match="job_id"):
        SubmitJobResponse.model_validate(
            {"job": {"workspace_id": "aqt_simulators", "resource_id": "simulator_no_noise"}}
        )


def test_device_run_end_to_end(device, mock_session):
    """``run`` transpiles a qiskit circuit through ``qiskit -> aqt_connector``, then submits it."""

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

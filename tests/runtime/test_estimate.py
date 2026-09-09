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

"""Resource estimator client tests using the public core schemas and a patched session."""

import sys
from unittest.mock import Mock, call, patch

import pyqasm
import pytest
from qbraid_core.exceptions import RequestsApiError
from qbraid_core.services.runtime import QuantumRuntimeClient, QuantumRuntimeServiceRequestError
from qbraid_core.services.runtime.schemas.estimate import Estimate, EstimateTarget

from qbraid.runtime import QbraidEstimate, QbraidProvider, estimate
from qbraid.runtime.exceptions import QbraidRuntimeError

QASM3 = 'OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[2] q;\nh q[0];\ncx q[0], q[1];\n'
QASM2 = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\nh q[0];\ncx q[0], q[1];\n'
DEVICE = "qbraid:qbraid:sim:qir-sv"
COLUMNS = [
    "deviceQrn",
    "shots",
    "minutes",
    "cost_exact",
    "cost_runtime",
    "cost_total",
    "quality",
    "basis",
]


@pytest.fixture
def estimate_data():
    """A completed estimate matching the shared v1 public contract."""
    return {
        "id": "estimate-123",
        "status": "COMPLETED",
        "createdAt": "2026-09-02T12:00:00Z",
        "features": {"numQubits": 2, "gateCount": 2, "twoQubitGateCount": 1, "depth": 2},
        "frontier": [
            {
                "deviceQrn": DEVICE,
                "shots": {"value": 100, "basis": "computed"},
                "minutes": {"value": 2, "interval": [1, 3], "basis": "historical-regression"},
                "cost": {
                    "exact": {"value": 1, "basis": "computed"},
                    "runtimeDependent": {"value": 2, "basis": "historical-regression"},
                    "total": {"value": 3, "basis": "historical-regression"},
                },
                "quality": {"value": 1, "basis": "computed"},
            }
        ],
        "infeasible": [{"deviceQrn": "qbraid:ionq:qpu:aria-1", "reason": "device max shots"}],
        "openQuestions": ["What observable are you measuring?"],
        "narrative": "Provide a target observable to refine this estimate.",
    }


@pytest.fixture
def estimate_client(estimate_data):
    """Patch only the HTTP session, retaining core response validation in the SDK."""
    client = Mock(spec=QuantumRuntimeClient)
    client.session.post.return_value.json.return_value = {
        "data": {**estimate_data, "status": "PENDING"}
    }
    client.session.get.return_value.json.return_value = {"data": estimate_data}
    return client


@pytest.mark.parametrize("program,alias", [(QASM2, "qasm2"), (QASM3, "qasm3")])
def test_estimate_qasm_body(estimate_client, program, alias):
    """QASM passes through unchanged; absent request fields stay null and wait stays local."""
    program = "// Preserve comments and whitespace.\n  " + program.replace(";\n", ";  \n")
    with patch("qbraid.runtime.native.provider.transpile") as convert:
        result = QbraidProvider(client=estimate_client).estimate(program, wait=False)
    convert.assert_not_called()
    estimate_client.session.post.assert_called_once_with(
        "/estimates",
        json={
            "program": {"format": alias, "data": program},
            "targets": None,
            "shots": None,
            "target": None,
            "narrate": True,
        },
    )
    assert isinstance(result, QbraidEstimate)
    assert result.id == "estimate-123"
    assert result.status == "PENDING"
    estimate_client.session.get.assert_not_called()


@pytest.mark.parametrize("kind", ["qiskit", "cirq", "braket"])
def test_estimate_transpiles_to_qasm3(estimate_client, kind):
    """Real supported circuits take the SDK conversion graph to serialized OpenQASM 3."""
    module = pytest.importorskip("braket.circuits" if kind == "braket" else kind)
    if kind == "qiskit":
        circuit = module.QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0, 1)
    elif kind == "cirq":
        qubits = module.LineQubit.range(2)
        circuit = module.Circuit(module.H(qubits[0]), module.CNOT(*qubits))
    else:
        circuit = module.Circuit().h(0).cnot(0, 1)
    QbraidProvider(client=estimate_client).estimate(circuit, shots=100, wait=False)
    body = estimate_client.session.post.call_args.kwargs["json"]
    assert body == {
        "program": {"format": "qasm3", "data": body["program"]["data"]},
        "targets": None,
        "shots": 100,
        "target": None,
        "narrate": True,
    }
    assert body["program"]["data"].startswith("OPENQASM 3.0;")
    parsed = pyqasm.loads(body["program"]["data"])
    parsed.unroll()
    assert parsed.num_qubits == 2
    assert parsed.depth() == 2


@pytest.mark.parametrize("as_dict", [True, False])
def test_estimate_options_and_default_wait(estimate_client, as_dict):
    """All estimation options reach the API and the default call waits for completion."""
    target = {"observableKind": "expectation", "tolerance": 0.1}
    result = QbraidProvider(client=estimate_client).estimate(
        QASM3,
        targets=[DEVICE],
        shots=100,
        target=target if as_dict else EstimateTarget.model_validate(target),
        narrate=False,
    )
    estimate_client.session.post.assert_called_once_with(
        "/estimates",
        json={
            "program": {"format": "qasm3", "data": QASM3},
            "targets": [DEVICE],
            "shots": 100,
            "target": target,
            "narrate": False,
        },
    )
    estimate_client.session.get.assert_called_once_with("/estimates/estimate-123")
    assert result.status == "COMPLETED"


def test_estimate_wait_polling(estimate_client, estimate_data):
    """Pending and running responses are polled on the same authenticated session."""
    estimate_client.session.get.side_effect = [
        Mock(json=Mock(return_value={"data": {**estimate_data, "status": status}}))
        for status in ["PENDING", "RUNNING", "COMPLETED"]
    ]
    result = QbraidProvider(client=estimate_client).estimate(QASM3, wait=False)
    with patch("qbraid.runtime.native.estimate.sleep") as sleep:
        assert result.wait(poll=0.25) is result
    assert sleep.call_args_list == [call(0.25), call(0.25)]
    assert estimate_client.session.get.call_count == 3
    assert result.wait() is result
    assert estimate_client.session.get.call_count == 3


@pytest.mark.parametrize("initial_failure", [True, False])
def test_estimate_failed(estimate_client, estimate_data, initial_failure):
    """An API failure includes its reason whether returned by POST or during polling."""
    failed = {**estimate_data, "status": "FAILED", "error": "estimator did not return in time"}
    if initial_failure:
        estimate_client.session.post.return_value.json.return_value = {"data": failed}
    else:
        estimate_client.session.get.return_value.json.return_value = {"data": failed}
    with pytest.raises(QbraidRuntimeError, match="estimator did not return in time"):
        QbraidProvider(client=estimate_client).estimate(QASM3)


def test_estimate_timeout(estimate_client, estimate_data):
    """An unfinished estimate raises TimeoutError rather than polling indefinitely."""
    estimate_client.session.get.return_value.json.return_value = {
        "data": {**estimate_data, "status": "RUNNING"}
    }
    result = QbraidProvider(client=estimate_client).estimate(QASM3, wait=False)
    with patch("qbraid.runtime.native.estimate.sleep") as sleep:
        with pytest.raises(TimeoutError, match="estimate-123"):
            result.wait(timeout=0)
    sleep.assert_not_called()


def test_estimate_refresh_and_properties(estimate_client, estimate_data):
    """Refreshing replaces the entire snapshot, including open questions and narrative."""
    result = QbraidProvider(client=estimate_client).estimate(QASM3, wait=False)
    estimate_data["openQuestions"] = ["How many shots?"]
    assert result.refresh() is result
    assert result.open_questions == ["How many shots?"]
    assert result.narrative == estimate_data["narrative"]
    assert result.features.numQubits == 2
    assert result.infeasible[0].reason == "device max shots"
    assert result.frontier[0].minutes.interval == (1, 3)


def test_estimate_dataframe(estimate_client, estimate_data):
    """Each frontier point becomes a row; unknown values remain missing, not zero."""
    pd = pytest.importorskip("pandas")
    point = estimate_data["frontier"][0]
    estimate_data["frontier"].append(
        {
            **point,
            "deviceQrn": "qbraid:ionq:qpu:forte-1",
            "quality": {"value": None, "basis": "unavailable"},
        }
    )
    result = QbraidEstimate(Estimate.model_validate(estimate_data), estimate_client)
    frame = result.to_dataframe()
    assert list(frame.columns) == COLUMNS
    assert len(frame) == 2
    assert frame.iloc[0].tolist() == [DEVICE, 100, 2, 1, 2, 3, 1, "historical-regression"]
    assert pd.isna(frame.iloc[1]["quality"])
    assert frame.iloc[1]["basis"] == "unavailable"


@pytest.mark.parametrize(
    "basis", ["computed", "historical-regression", "assumed-default", "unavailable"]
)
def test_estimate_dataframe_weakest_basis(estimate_client, estimate_data, basis):
    """The row basis accounts for every quantity, including a weaker quality basis."""
    pytest.importorskip("pandas")
    model = Estimate.model_validate(estimate_data)
    point = model.frontier[0]
    point.minutes.basis = "computed"
    point.cost.runtimeDependent.basis = "computed"
    point.cost.total.basis = "computed"
    point.quality.basis = basis
    assert QbraidEstimate(model, estimate_client).to_dataframe().iloc[0]["basis"] == basis


def test_estimate_empty_dataframe(estimate_client, estimate_data):
    """An empty frontier retains the documented DataFrame columns."""
    pytest.importorskip("pandas")
    estimate_data["frontier"] = []
    frame = QbraidEstimate(Estimate.model_validate(estimate_data), estimate_client).to_dataframe()
    assert frame.empty
    assert list(frame.columns) == COLUMNS


def test_estimate_without_pandas(estimate_client):
    """Pandas is needed only for to_dataframe, with an actionable installation hint."""
    with patch.dict(sys.modules, {"pandas": None}):
        result = QbraidProvider(client=estimate_client).estimate(QASM3)
        with pytest.raises(ImportError, match="pip install pandas"):
            result.to_dataframe()


def test_estimate_convenience():
    """The public convenience function constructs a default provider and forwards options."""
    with patch("qbraid.runtime.native.provider.QbraidProvider") as provider:
        result = estimate(QASM3, targets=[DEVICE], shots=100, narrate=False, wait=False)
    provider.assert_called_once_with()
    provider.return_value.estimate.assert_called_once_with(
        QASM3, targets=[DEVICE], shots=100, target=None, narrate=False, wait=False
    )
    assert result is provider.return_value.estimate.return_value


@pytest.mark.parametrize("options", [{"shots": 0}, {"target": {"tolerance": 1}}])
def test_estimate_invalid_request(estimate_client, options):
    """Core validation rejects invalid options before sending a request."""
    with pytest.raises(ValueError):
        QbraidProvider(client=estimate_client).estimate(QASM3, **options)
    estimate_client.session.post.assert_not_called()


def test_estimate_rejects_batch(estimate_client):
    """Estimation never silently submits the first item of a batch."""
    with pytest.raises(ValueError, match="single program"):
        QbraidProvider(client=estimate_client).estimate([QASM3])
    estimate_client.session.post.assert_not_called()


@pytest.mark.parametrize("method", ["post", "get"])
def test_estimate_request_error(estimate_client, method):
    """HTTP failures use the same runtime-service exception as native job requests."""
    getattr(estimate_client.session, method).side_effect = RequestsApiError("unavailable")
    with pytest.raises(QuantumRuntimeServiceRequestError, match="unavailable"):
        QbraidProvider(client=estimate_client).estimate(QASM3)

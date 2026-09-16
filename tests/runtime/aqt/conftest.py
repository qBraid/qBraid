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
Pytest configuration and shared fixtures for the AQT runtime tests.

The AQT suite (provider, device, job, and the ``qiskit -> aqt_connector`` conversion) exercises real
``aqt_connector`` pydantic models and the transpiler edge, both of which require the optional
``aqt-connector`` dependency (the ``aqt`` extra). That package conflicts with ``pasqal-cloud``
(on ``auth0-python``) so it is not installed in the main test environment; skip the whole
directory when it is unavailable. CI runs this suite through the ``unit-tests-aqt`` tox env,
which installs the extra on its own.

When ``aqt-connector`` *is* installed, the fixtures below are shared across the split test
modules: the native-circuit factory (``aqt_circuit``), the raw arnica resource body
(``simulator_resource``), a fully mocked ``AQTSession`` (``mock_session``), a simulator
``TargetProfile`` (``profile``), and an ``AQTDevice`` backed by the mocked session (``device``).
No network access occurs in any test here — the live-credential coverage lives in
``test_aqt_remote.py``, which is gated behind the ``remote`` marker.

Every arnica payload below is a raw dict passed through the ``aqt-connector`` model that the
session validates with, so these fixtures cannot drift into a shape the API never returns.
"""

from __future__ import annotations

import importlib.util

collect_ignore = []
if importlib.util.find_spec("aqt_connector") is None:
    collect_ignore = [
        "test_aqt_conversion.py",
        "test_aqt_device.py",
        "test_aqt_job.py",
        "test_aqt_provider.py",
        "test_aqt_remote.py",
    ]
else:
    from unittest.mock import MagicMock

    import pytest
    from aqt_connector.models.arnica.response_bodies.jobs import SubmitJobResponse
    from aqt_connector.models.arnica.response_bodies.resources import ResourceDetails
    from aqt_connector.models.circuits import Circuit, QuantumCircuit
    from aqt_connector.models.operations import GateR, GateRXX, GateRZ, Measure, OperationModel

    from qbraid.runtime.aqt import AQTDevice, AQTProvider, AQTSession

    # Arnica payloads mirroring the exact production data structure. The shape, key set, field
    # types and resource topology were captured verbatim from the production arnica API
    # (2026-07-31) using the qBraid staging service account, then passed through the
    # aqt-connector models below rather than hand-built, so these fixtures cannot drift into a
    # shape arnica never returns.
    #
    # NOTE: every number under ``characterisation`` -- gate fidelities, SPAM, T1/T2, gate and
    # readout durations -- is MOCK DATA, not the measured values AQT reports. The structure is
    # real; the calibration figures are placeholders, so real device performance data is not
    # published here. Re-capture the structure via tests/runtime/aqt/test_aqt_remote.py when
    # AQT's API changes, and re-mock the numbers before committing.
    WORKSPACES: list[dict] = [
        {
            "id": "qbraid",
            "accepting_job_submissions": True,
            "jobs_being_processed": False,
            "resources": [{"id": "ibex", "name": "Ibex", "type": "device"}],
        },
        {
            "id": "aqt_simulators",
            "accepting_job_submissions": True,
            "jobs_being_processed": True,
            "resources": [
                {"id": "simulator_no_noise", "name": "Ideal Simulator", "type": "simulator"},
                {"id": "simulator_noise", "name": "Noisy Simulator", "type": "simulator"},
            ],
        },
    ]

    # Every ``GET /resources/{id}`` body the account can see, keyed by resource id as the
    # API serves them: the ``qbraid/ibex`` QPU and AQT's two public simulators. Note that
    # ``characterisation`` is populated on every real resource, including the simulators.
    RESOURCES: dict[str, dict] = {
        "ibex": {
            "id": "ibex",
            "name": "Ibex",
            "type": "device",
            "status": "unavailable",
            "available_qubits": 12,
            "status_updated_at": "2026-07-31T17:55:50.433901Z",
            "characterisation": {
                "single_qubit_gate_fidelity": {
                    "0": {"value": 99.9, "uncertainty": 0.01},
                    "1": {"value": 99.9, "uncertainty": 0.01},
                    "2": {"value": 99.9, "uncertainty": 0.01},
                    "3": {"value": 99.9, "uncertainty": 0.01},
                    "4": {"value": 99.9, "uncertainty": 0.01},
                    "5": {"value": 99.9, "uncertainty": 0.01},
                    "6": {"value": 99.9, "uncertainty": 0.01},
                    "7": {"value": 99.9, "uncertainty": 0.01},
                    "8": {"value": 99.9, "uncertainty": 0.01},
                    "9": {"value": 99.9, "uncertainty": 0.01},
                    "10": {"value": 99.9, "uncertainty": 0.01},
                    "11": {"value": 99.9, "uncertainty": 0.01},
                },
                "mean_two_qubit_gate_fidelity": {"value": 99.0, "uncertainty": 0.1},
                "spam_fidelity_lower_bound": 99.5,
                "t2_coherence_time_s": {"value": 0.15, "uncertainty": 0.04},
                "t1_s": {"value": 1.0, "uncertainty": 0.01},
                "readout_time_micros": 1000.0,
                "single_qubit_gate_duration_micros": 50.0,
                "two_qubit_gate_duration_micros": 300.0,
                "updated_at": "2026-01-01T00:00:00Z",
            },
        },
        "simulator_no_noise": {
            "id": "simulator_no_noise",
            "name": "Ideal Simulator",
            "type": "simulator",
            "status": "online",
            "available_qubits": 12,
            "status_updated_at": "2026-07-31T17:55:50.447258Z",
            "characterisation": {
                "single_qubit_gate_fidelity": {
                    "0": {"value": 100.0, "uncertainty": 0.0},
                    "1": {"value": 100.0, "uncertainty": 0.0},
                    "2": {"value": 100.0, "uncertainty": 0.0},
                    "3": {"value": 100.0, "uncertainty": 0.0},
                    "4": {"value": 100.0, "uncertainty": 0.0},
                    "5": {"value": 100.0, "uncertainty": 0.0},
                    "6": {"value": 100.0, "uncertainty": 0.0},
                    "7": {"value": 100.0, "uncertainty": 0.0},
                    "8": {"value": 100.0, "uncertainty": 0.0},
                    "9": {"value": 100.0, "uncertainty": 0.0},
                    "10": {"value": 100.0, "uncertainty": 0.0},
                    "11": {"value": 100.0, "uncertainty": 0.0},
                },
                "mean_two_qubit_gate_fidelity": {"value": 100.0, "uncertainty": 0.0},
                "spam_fidelity_lower_bound": 100.0,
                "t2_coherence_time_s": {"value": 0.15, "uncertainty": 0.04},
                "t1_s": {"value": 1.0, "uncertainty": 0.01},
                "readout_time_micros": 0.0,
                "single_qubit_gate_duration_micros": 0.0,
                "two_qubit_gate_duration_micros": 0.0,
                "updated_at": "2026-01-01T00:00:00Z",
            },
        },
        "simulator_noise": {
            "id": "simulator_noise",
            "name": "Noisy Simulator",
            "type": "simulator",
            "status": "online",
            "available_qubits": 12,
            "status_updated_at": "2026-07-31T17:55:50.467336Z",
            "characterisation": {
                "single_qubit_gate_fidelity": {
                    "0": {"value": 99.5, "uncertainty": 0.0},
                    "1": {"value": 99.5, "uncertainty": 0.0},
                    "2": {"value": 99.5, "uncertainty": 0.0},
                    "3": {"value": 99.5, "uncertainty": 0.0},
                    "4": {"value": 99.5, "uncertainty": 0.0},
                    "5": {"value": 99.5, "uncertainty": 0.0},
                    "6": {"value": 99.5, "uncertainty": 0.0},
                    "7": {"value": 99.5, "uncertainty": 0.0},
                    "8": {"value": 99.5, "uncertainty": 0.0},
                    "9": {"value": 99.5, "uncertainty": 0.0},
                    "10": {"value": 99.5, "uncertainty": 0.0},
                    "11": {"value": 99.5, "uncertainty": 0.0},
                },
                "mean_two_qubit_gate_fidelity": {"value": 99.0, "uncertainty": 0.0},
                "spam_fidelity_lower_bound": 100.0,
                "t2_coherence_time_s": {"value": 0.15, "uncertainty": 0.04},
                "t1_s": {"value": 1.0, "uncertainty": 0.01},
                "readout_time_micros": 0.0,
                "single_qubit_gate_duration_micros": 0.0,
                "two_qubit_gate_duration_micros": 0.0,
                "updated_at": "2026-01-01T00:00:00Z",
            },
        },
    }

    @pytest.fixture
    def aqt_circuit():
        """Factory building a minimal, API-valid native AQT ``QuantumCircuit``.

        Angles are already in the API's units of pi and within the accepted ranges, so the model
        validates on construction. ``repetitions`` is the placeholder the device overwrites.
        """

        def _build(number_of_qubits: int = 2) -> QuantumCircuit:
            circuit = Circuit(
                root=[
                    OperationModel(root=GateRZ(phi=0.5, qubit=0)),
                    OperationModel(root=GateR(phi=0.0, theta=0.5, qubit=0)),
                    OperationModel(root=GateRXX(theta=0.5, qubits=[0, 1])),
                    OperationModel(root=Measure()),
                ]
            )
            return QuantumCircuit(
                repetitions=1, quantum_circuit=circuit, number_of_qubits=number_of_qubits
            )

        return _build

    @pytest.fixture
    def simulator_resource() -> dict:
        """The real ``GET /resources/simulator_no_noise`` body (a fresh copy per test)."""
        return dict(RESOURCES["simulator_no_noise"])

    @pytest.fixture
    def device_resource() -> dict:
        """The real ``GET /resources/ibex`` QPU body (a fresh copy per test)."""
        return dict(RESOURCES["ibex"])

    @pytest.fixture
    def workspaces() -> list[dict]:
        """The real ``GET /workspaces`` body (a fresh copy per test)."""
        return [dict(workspace) for workspace in WORKSPACES]

    @pytest.fixture
    def resources() -> dict[str, dict]:
        """Every real ``GET /resources/{id}`` body, keyed by resource id."""
        return {rid: dict(body) for rid, body in RESOURCES.items()}

    @pytest.fixture
    def mock_session() -> MagicMock:
        """A fully mocked ``AQTSession`` (no network).

        Returns the same validated models the real session returns, so tests exercise the
        attribute access the production code performs rather than a looser dict shape.
        """
        session = MagicMock(spec=AQTSession)
        session.get_resource.return_value = ResourceDetails.model_validate(
            RESOURCES["simulator_no_noise"]
        )
        session.submit_job.return_value = SubmitJobResponse.model_validate(
            {
                "job": {
                    "job_id": "6f1b6a1e-2f1e-4c3a-9d5b-1f0a2b3c4d5e",
                    "job_type": "quantum_circuit",
                    "label": "qbraid",
                    "workspace_id": "aqt_simulators",
                    "resource_id": "simulator_no_noise",
                },
                "response": {"status": "queued"},
            }
        )
        return session

    @pytest.fixture
    def profile():
        """A ``TargetProfile`` for the ``aqt_simulators/simulator_no_noise`` resource."""
        return AQTProvider._build_profile(
            ResourceDetails.model_validate(RESOURCES["simulator_no_noise"]), "aqt_simulators"
        )

    @pytest.fixture
    def device(profile, mock_session) -> AQTDevice:
        """An ``AQTDevice`` backed by the mocked session."""
        return AQTDevice(profile, mock_session)

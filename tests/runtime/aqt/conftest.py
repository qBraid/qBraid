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

The AQT suite (provider, device, job, and the ``qiskit -> aqt`` conversion) exercises real
``aqt_connector`` pydantic models and the transpiler edge, both of which require the optional
``aqt-connector`` dependency (the ``aqt`` extra). That package conflicts with ``pasqal-cloud``
(on ``auth0-python``) so it is not installed in the main test environment; skip the whole
directory when it is unavailable.

When ``aqt-connector`` *is* installed, the fixtures below are shared across the split test
modules: the native-circuit factory (``aqt_circuit``), a fully mocked ``AQTSession``
(``mock_session``), a simulator ``TargetProfile`` (``profile``), and an ``AQTDevice`` backed by
the mocked session (``device``). No network access occurs in any test.
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
    ]
else:
    from unittest.mock import MagicMock

    import pytest
    from aqt_connector.models.circuits import Circuit, QuantumCircuit
    from aqt_connector.models.operations import GateR, GateRXX, GateRZ, Measure, OperationModel

    from qbraid.runtime.aqt import AQTDevice, AQTProvider, AQTSession

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
    def mock_session() -> MagicMock:
        """A fully mocked ``AQTSession`` (no network)."""
        session = MagicMock(spec=AQTSession)
        session.get_resource.return_value = {
            "id": "sim1",
            "status": "online",
            "available_qubits": 20,
        }
        session.submit_job.return_value = {"job": {"job_id": "job-1"}}
        return session

    @pytest.fixture
    def profile():
        """A ``TargetProfile`` for the ``default/sim1`` simulator resource."""
        return AQTProvider._build_profile(
            {"id": "sim1", "type": "simulator", "available_qubits": 20}, "default"
        )

    @pytest.fixture
    def device(profile, mock_session) -> AQTDevice:
        """An ``AQTDevice`` backed by the mocked session."""
        return AQTDevice(profile, mock_session)

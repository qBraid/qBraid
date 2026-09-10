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

# pylint: disable=too-many-arguments,missing-function-docstring

"""
Fixtures for the QDI runtime tests: an in-memory QDI client and the device
descriptors the two working-group implementations actually publish.

"""

import copy
import itertools
import json

import pytest

# Captured verbatim from ``OqtopusQdiClient.discover()`` against
# https://demo-api.oqtopus.io on 2026-09-10 (qdi-oqtopus @ 46f8b07).
OQTOPUS_QULACS = {
    "device_id": "qulacs",
    "display_name": "Qulacs Simulator",
    "supported_auth_methods": ["token"],
    "supported_task_types": ["openqasm3"],
    "supported_extensions": ["name", "description", "transpiler_info", "mitigation_info"],
    "is_ready": True,
    "supports_estimation": False,
    "num_qubits": 16,
}

# The reference server's default device (qdi-demo ``mock_device_config.json`` @ c4452ac);
# ``max_shots`` and friends are demo-only keys the descriptor must carry through as extras.
DEMO_MOCK = {
    "device_id": "mock_qdi_qubit_v1",
    "display_name": "Mock QDI QPU",
    "supported_auth_methods": ["token"],
    "supported_task_types": ["openqasm3", "openqasm2", "qir"],
    "supported_extensions": ["transpiler_info"],
    "is_ready": True,
    "supports_estimation": True,
    "num_qubits": 32,
    "max_shots": 10000,
}

QASM3_BELL = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c = measure q;
"""

QASM2_BELL = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;
"""


class FakeQdiError(Exception):
    """Stand-in for a vendor client's error type: carries the QDI status as ``status``."""

    def __init__(self, status: int, detail: str):
        self.status = status
        super().__init__(detail)


class FakeQdiClient:
    """In-memory QDI v0.2 device.

    ``auth_before_discover=True`` reproduces OQTOPUS, whose Discover rejects an
    unauthenticated call (gap G4); the default reproduces the reference server,
    whose Discover is open. Each ``send`` walks ``statuses`` one ``monitor`` call
    at a time (default: already COMPLETED), then returns ``counts`` from ``receive``.
    """

    def __init__(
        self,
        descriptors=None,
        *,
        auth_before_discover=False,
        expected_credentials=None,
        statuses=(2,),
        counts=None,
        result_type="counts",
    ):
        self.descriptors = copy.deepcopy(descriptors if descriptors is not None else [DEMO_MOCK])
        self.auth_before_discover = auth_before_discover
        self.expected_credentials = expected_credentials
        self.statuses = list(statuses)
        self.counts = counts if counts is not None else {"00": 52, "11": 48}
        self.result_type = result_type
        self.authenticated = False
        self.calls: list[tuple] = []
        self.tasks: dict[str, dict] = {}
        self._ids = itertools.count(1)

    def discover(self) -> dict:
        self.calls.append(("discover",))
        if self.auth_before_discover and not self.authenticated:
            raise FakeQdiError(2, "authenticate() must be called before this operation.")
        return {"devices": copy.deepcopy(self.descriptors)}

    def authenticate(self, device_id: str, credentials_dict: dict) -> None:
        self.calls.append(("authenticate", device_id, credentials_dict))
        if self.expected_credentials is not None and credentials_dict != self.expected_credentials:
            raise FakeQdiError(2, "Authentication failed (invalid token).")
        self.authenticated = True

    def send(self, device_id, task_payload, task_type, shots=100, extensions=None) -> str:
        self.calls.append(("send", device_id, task_payload, task_type, shots, extensions))
        descriptor = next(d for d in self.descriptors if d["device_id"] == device_id)
        if task_type not in descriptor["supported_task_types"]:
            raise FakeQdiError(5, f"Unsupported task_type '{task_type}'.")
        task_id = f"task-{next(self._ids)}"
        self.tasks[task_id] = {"remaining": list(self.statuses), "shots": shots}
        return task_id

    def monitor(self, device_id, task_id) -> tuple[int, dict]:
        self.calls.append(("monitor", device_id, task_id))
        remaining = self.tasks[task_id]["remaining"]
        status = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        return status, {"queue_position": len(remaining) - 1}

    def receive(self, device_id, task_id) -> tuple[str, str]:
        self.calls.append(("receive", device_id, task_id))
        return json.dumps(self.counts), self.result_type

    def estimate_resources(self, device_id, task_payload, task_type, shots=100, extensions=None):
        self.calls.append(("estimate", device_id, task_payload, task_type, shots, extensions))
        return {"device_id": device_id, "shots": shots, "shots_duration_sec": 0.02 * shots}


class NeedsArgsQdiClient(FakeQdiClient):
    """A QDI client whose constructor is not argument-free."""

    def __init__(self, base_url: str):  # pylint: disable=super-init-not-called
        self.base_url = base_url


@pytest.fixture
def fake_client():
    """A reference-server-shaped fake with the mock device and open Discover."""
    return FakeQdiClient()


@pytest.fixture
def oqtopus_client():
    """An OQTOPUS-shaped fake: one qulacs device, Discover requires Authenticate first."""
    return FakeQdiClient(
        [OQTOPUS_QULACS],
        auth_before_discover=True,
        expected_credentials={"base_url": "https://demo-api.oqtopus.io", "api_token": "tok"},
    )

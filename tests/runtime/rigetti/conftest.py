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
#
# pylint: disable=redefined-outer-name,import-outside-toplevel

"""Shared fixtures for Rigetti runtime tests."""

from unittest.mock import MagicMock

import pytest

from qbraid.programs.experiment import ExperimentType
from qbraid.programs.spec import ProgramSpec
from qbraid.runtime import TargetProfile

DEVICE_ID = "Ankaa-3"
DUMMY_TOKEN = "dummy-refresh-token"
DUMMY_CLIENT_ID = "dummy-client-id"
DUMMY_ISSUER = "https://dummy.issuer.example.com"
DUMMY_JOB_ID = "job-abc-123"

# Default ro_sources mapping used by the rigetti_job fixture.
# Maps declared memory references to hardware readout keys.
DEFAULT_RO_SOURCES = {
    "ro[0]": "q0_readout",
    "ro[1]": "q1_readout",
}


@pytest.fixture()
def qpu_profile() -> TargetProfile:
    """A TargetProfile representing a real QPU (simulator=False)."""
    pyquil = pytest.importorskip("pyquil")
    return TargetProfile(
        device_id=DEVICE_ID,
        simulator=False,
        experiment_type=ExperimentType.GATE_MODEL,
        program_spec=ProgramSpec(pyquil.Program, serialize=lambda program: program.out()),
        num_qubits=84,
        provider_name="rigetti",
    )


@pytest.fixture()
def mock_qcs_client() -> MagicMock:
    """A generic mock replacing qcs_sdk.client.QCSClient."""
    return MagicMock(name="QCSClient")


@pytest.fixture()
def rigetti_device(qpu_profile: TargetProfile, mock_qcs_client: MagicMock):
    """A RigettiDevice backed by a mock QCSClient and QPU profile."""
    pytest.importorskip("pyquil")
    from qbraid.runtime.rigetti import RigettiDevice

    return RigettiDevice(profile=qpu_profile, qcs_client=mock_qcs_client)


@pytest.fixture()
def rigetti_job(rigetti_device):
    """A RigettiJob in INITIALIZING state with num_shots=3 and default ro_sources."""
    pytest.importorskip("pyquil")
    from qbraid.runtime.rigetti import RigettiJob

    return RigettiJob(
        job_id=DUMMY_JOB_ID,
        device=rigetti_device,
        num_shots=3,
        ro_sources=DEFAULT_RO_SOURCES,
    )


@pytest.fixture()
def mock_isa_response() -> MagicMock:
    """
    Mimics the ISA object returned by get_instruction_set_architecture.
    architecture.nodes is a list of Node-like objects each with a .node_id attribute.
    """
    node_ids = [0, 1, 2, 3, 4]
    nodes = [MagicMock(node_id=nid) for nid in node_ids]
    isa = MagicMock()
    isa.architecture.nodes = nodes
    return isa

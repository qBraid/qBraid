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

"""
Unit tests for batch job support (as_batch=True).

Tests batch submission through QbraidDevice and batch result parsing
through QbraidJob.result().
"""

from unittest.mock import patch

import pytest

from qbraid._caching import cache_disabled
from qbraid.runtime import BatchResult, Result
from qbraid.runtime.group import GroupJobSession
from qbraid.runtime.native import QbraidProvider
from qbraid.runtime.native.job import QbraidJob

from .._resources import (
    JOB_DATA_BATCH_EQUAL1,
    JOB_DATA_EQUAL1,
    RESULTS_DATA_BATCH_EQUAL1,
    MockClient,
)


@pytest.fixture
def client():
    """Create a fresh MockClient for each test."""
    return MockClient()


@pytest.fixture
def device(client):
    """Create a QbraidDevice backed by the MockClient via QbraidProvider."""
    provider = QbraidProvider(client=client)
    with cache_disabled(provider):
        return provider.get_device("qbraid:equal1:sim:bell-1")


QASM_H = (
    'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
    "qreg q[2];\ncreg c[1];\nh q[0];\nmeasure q[0] -> c[0];"
)
QASM_X = (
    'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
    "qreg q[2];\ncreg c[1];\nx q[0];\nmeasure q[0] -> c[0];"
)
QASM_CX = (
    'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
    "qreg q[2];\ncreg c[2];\ncx q[0],q[1];\n"
    "measure q[0] -> c[0];\nmeasure q[1] -> c[1];"
)


@pytest.fixture
def batch_programs():
    """Three QASM2 programs for batch submission."""
    return [QASM_H, QASM_X, QASM_CX]


# ── Batch Submission Tests ────────────────────────────────────────────


class TestBatchSubmission:
    """Tests for device.run(programs, as_batch=True) submission flow."""

    def test_batch_submit_returns_single_job(self, device, batch_programs):
        """Batch submit returns a single QbraidJob (not a list)."""
        job = device.run(batch_programs, as_batch=True, shots=100)
        assert isinstance(job, QbraidJob)

    def test_batch_submit_calls_create_job_once(self, device, batch_programs):
        """Batch submit calls client.create_job exactly once with program as list."""
        with patch.object(device.client, "create_job", wraps=device.client.create_job) as spy:
            device.run(batch_programs, as_batch=True, shots=100)
            assert spy.call_count == 1
            request = spy.call_args[0][0]
            assert isinstance(request.program, list)
            assert len(request.program) == 3

    def test_batch_submit_unsupported_device_raises(self, client):
        """as_batch=True on a device without batch support raises ValueError."""
        provider = QbraidProvider(client=client)
        with cache_disabled(provider):
            qir_device = provider.get_device("qbraid:qbraid:sim:qir-sv")
        programs = [QASM_H, QASM_X]
        with pytest.raises(ValueError, match="not supported"):
            qir_device.run(programs, as_batch=True)

    def test_batch_submit_non_list_raises(self, device):
        """as_batch=True with a single (non-list) program raises ValueError."""
        single = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nh q[0];'
        with pytest.raises(ValueError, match="require a list"):
            device.run(single, as_batch=True)

    def test_batch_submit_with_group_session(self, device, batch_programs):
        """Batch submit inside a GroupJobSession passes groupJobQrn."""
        with GroupJobSession(client=device.client, name="test-group") as session:
            job = device.run(batch_programs, as_batch=True, shots=100)
            assert isinstance(job, QbraidJob)
            assert job in session.jobs


# ── Batch Result Tests ────────────────────────────────────────────────


class TestBatchResult:
    """Tests for QbraidJob.result() with batch jobs (numCircuits > 1)."""

    def test_batch_result_returns_batch_result(self, device, client):
        """result() for a batch job returns a BatchResult."""
        job = QbraidJob(
            job_id=JOB_DATA_BATCH_EQUAL1["jobQrn"],
            device=device,
            client=client,
        )
        result = job.result()
        assert isinstance(result, BatchResult)
        assert result.num_circuits == 3

    def test_batch_result_per_circuit_data(self, device, client):
        """Each per-circuit Result has the correct measurementCounts."""
        job = QbraidJob(
            job_id=JOB_DATA_BATCH_EQUAL1["jobQrn"],
            device=device,
            client=client,
        )
        result = job.result()
        for i, circuit_result in enumerate(result.results):
            assert (
                circuit_result.data.get_counts()
                == RESULTS_DATA_BATCH_EQUAL1[i]["measurementCounts"]
            )

    def test_batch_result_aggregate_counts(self, device, client):
        """Aggregate data.get_counts() returns a list of all circuit counts."""
        job = QbraidJob(
            job_id=JOB_DATA_BATCH_EQUAL1["jobQrn"],
            device=device,
            client=client,
        )
        result = job.result()
        counts = result.data.get_counts()
        assert isinstance(counts, list)
        assert len(counts) == 3

    def test_batch_result_details_indexed(self, device, client):
        """details returns a list of per-circuit detail dicts."""
        job = QbraidJob(
            job_id=JOB_DATA_BATCH_EQUAL1["jobQrn"],
            device=device,
            client=client,
        )
        result = job.result()
        details = result.details
        assert isinstance(details, list)
        assert len(details) == 3

    def test_batch_result_metadata(self, device, client):
        """BatchResult has correct device_id, job_id, and success flag."""
        job = QbraidJob(
            job_id=JOB_DATA_BATCH_EQUAL1["jobQrn"],
            device=device,
            client=client,
        )
        result = job.result()
        assert result.device_id == JOB_DATA_BATCH_EQUAL1["deviceQrn"]
        assert result.job_id == JOB_DATA_BATCH_EQUAL1["jobQrn"]
        assert result.success is True

    def test_single_circuit_result_unchanged(self, device, client):
        """Single-circuit job still returns a single Result (not BatchResult)."""
        job = QbraidJob(
            job_id=JOB_DATA_EQUAL1["jobQrn"],
            device=device,
            client=client,
        )
        result = job.result()
        assert isinstance(result, Result)
        assert not isinstance(result, BatchResult)

    def test_batch_result_failed_job(self, device, client):
        """A failed batch job returns a BatchResult with success=False."""
        original_status = JOB_DATA_BATCH_EQUAL1["status"]
        JOB_DATA_BATCH_EQUAL1["status"] = "FAILED"
        try:
            job = QbraidJob(
                job_id=JOB_DATA_BATCH_EQUAL1["jobQrn"],
                device=device,
                client=client,
            )
            result = job.result()
            assert isinstance(result, BatchResult)
            assert result.num_circuits == 3
            assert result.success is False
            for circuit_result in result.results:
                assert circuit_result.success is False
        finally:
            JOB_DATA_BATCH_EQUAL1["status"] = original_status

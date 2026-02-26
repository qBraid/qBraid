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
End-to-end tests: CUDA-Q kernels executed on real QPUs/simulators via qBraid API.

These tests require:
  1. A valid qBraid API key (set QBRAID_API_KEY env var)
  2. The cudaq package installed
  3. Network access to the qBraid API
  4. The target devices to be ONLINE and seeded in the device catalog

Run with:
    QBRAID_API_KEY=<your-key> pytest tests/runtime/test_cudaq_e2e.py -v -s

"""
from __future__ import annotations

import os

import pytest

try:
    import cudaq

    from qbraid.programs.gate_model.cudaq import CudaQKernel
    from qbraid.runtime.native.provider import QbraidProvider

    _deps_available = True
except ImportError:
    _deps_available = False

_api_key = os.environ.get("QBRAID_API_KEY", "")
_skip_reason = ""
if not _deps_available:
    _skip_reason = "cudaq or qbraid not installed"
elif not _api_key:
    _skip_reason = "QBRAID_API_KEY env var not set"

pytestmark = pytest.mark.skipif(bool(_skip_reason), reason=_skip_reason)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def provider():
    """A QbraidProvider authenticated with the API key from the environment."""
    return QbraidProvider(api_key=_api_key)


@pytest.fixture
def bell_kernel():
    """A simple 2-qubit Bell state kernel."""
    kernel = cudaq.make_kernel()
    qubits = kernel.qalloc(2)
    kernel.h(qubits[0])
    kernel.cx(qubits[0], qubits[1])
    kernel.mz(qubits)
    return kernel


@pytest.fixture
def ghz3_kernel():
    """A 3-qubit GHZ state kernel."""
    kernel = cudaq.make_kernel()
    qubits = kernel.qalloc(3)
    kernel.h(qubits[0])
    kernel.cx(qubits[0], qubits[1])
    kernel.cx(qubits[1], qubits[2])
    kernel.mz(qubits)
    return kernel


# ---------------------------------------------------------------------------
# E2E Test: List devices
# ---------------------------------------------------------------------------


class TestDeviceDiscovery:
    """Verify qBraid API returns CUDA-Q simulator devices."""

    def test_list_devices(self, provider):
        """The provider should list at least one device."""
        devices = provider.get_devices()
        assert len(devices) > 0
        print(f"\nFound {len(devices)} devices:")
        for d in devices:
            print(f"  {d.id} — {d.profile.name or 'unnamed'} (qubits={d.num_qubits})")

    @pytest.mark.parametrize(
        "device_qrn",
        [
            "qbraid:qbraid:sim:custatevec",
            "qbraid:qbraid:sim:cutensornet",
            "qbraid:qbraid:sim:cudensitymat",
            "qbraid:qbraid:sim:qpp",
            "qbraid:qbraid:sim:stim",
            "qbraid:qbraid:sim:dynamics",
        ],
    )
    def test_get_cudaq_device(self, provider, device_qrn):
        """Each CUDA-Q simulator device should be retrievable by QRN."""
        try:
            device = provider.get_device(device_qrn)
            assert device.id == device_qrn
            assert device.simulator is True
            print(f"\n  {device_qrn}: ONLINE, {device.num_qubits} qubits")
        except Exception as exc:
            pytest.skip(f"Device {device_qrn} not available: {exc}")


# ---------------------------------------------------------------------------
# E2E Test: Submit to qBraid-managed simulators
# ---------------------------------------------------------------------------


class TestCudaqSimulatorExecution:
    """Submit CUDA-Q kernels to qBraid-managed simulators and verify results."""

    def _run_and_verify_bell(self, provider, device_qrn, bell_kernel, shots=100):
        """Helper: submit Bell state to a device and verify results."""
        try:
            device = provider.get_device(device_qrn)
        except Exception as exc:
            pytest.skip(f"Device {device_qrn} not available: {exc}")

        job = device.run(bell_kernel, shots=shots)
        print(f"\n  Job submitted: {job.id}")

        # Wait for completion (timeout 5 min)
        job.wait_for_final_state(timeout=300, poll_interval=5)

        result = job.result()
        assert result.success, f"Job failed: {result.details}"

        counts = result.data.get_counts()
        print(f"  Counts: {counts}")

        # Bell state should produce mostly "00" and "11"
        assert len(counts) > 0
        for bitstring in counts:
            assert all(c in "01" for c in bitstring), f"Invalid bitstring: {bitstring}"

        total = sum(counts.values())
        assert total == shots, f"Expected {shots} total shots, got {total}"

        return counts

    def test_bell_on_qpp(self, provider, bell_kernel):
        """Bell state on QPP CPU simulator."""
        counts = self._run_and_verify_bell(
            provider, "qbraid:qbraid:sim:qpp", bell_kernel
        )
        # QPP is a state-vector sim — should only give "00" and "11"
        assert set(counts.keys()).issubset({"00", "11"})

    def test_bell_on_custatevec(self, provider, bell_kernel):
        """Bell state on cuStateVec GPU simulator."""
        self._run_and_verify_bell(
            provider, "qbraid:qbraid:sim:custatevec", bell_kernel
        )

    def test_bell_on_stim(self, provider, bell_kernel):
        """Bell state on Stim Clifford simulator (Bell is a Clifford circuit)."""
        self._run_and_verify_bell(
            provider, "qbraid:qbraid:sim:stim", bell_kernel
        )

    def test_ghz3_on_qpp(self, provider, ghz3_kernel):
        """3-qubit GHZ on QPP — should give '000' and '111' only."""
        try:
            device = provider.get_device("qbraid:qbraid:sim:qpp")
        except Exception as exc:
            pytest.skip(f"QPP device not available: {exc}")

        job = device.run(ghz3_kernel, shots=200)
        job.wait_for_final_state(timeout=300, poll_interval=5)
        result = job.result()
        assert result.success

        counts = result.data.get_counts()
        print(f"\n  GHZ3 counts: {counts}")
        assert set(counts.keys()).issubset({"000", "111"})


# ---------------------------------------------------------------------------
# E2E Test: Submit to real QPU hardware (via qBraid)
# ---------------------------------------------------------------------------


class TestCudaqQPUExecution:
    """Submit CUDA-Q kernels to real QPU hardware through qBraid.

    These tests target real hardware and may incur costs. They are
    parameterized by QPU QRN so you can run specific ones:

        pytest -k "test_bell_on_qpu[aws:ionq:qpu:aria-1]" -v -s
    """

    @pytest.mark.parametrize(
        "device_qrn",
        [
            # IonQ via AWS
            "aws:ionq:qpu:aria-1",
            "aws:ionq:qpu:aria-2",
            "aws:ionq:qpu:forte-1",
            # IonQ direct
            "ionq:ionq:qpu:aria-1",
            # Quantinuum via Azure
            "azure:quantinuum:qpu:h1-1",
            # IQM via AWS
            "aws:iqm:qpu:garnet",
            # Rigetti via Azure
            "azure:rigetti:qpu:ankaa-2",
        ],
    )
    def test_bell_on_qpu(self, provider, bell_kernel, device_qrn):
        """Submit a Bell state to a real QPU and verify measurement results."""
        try:
            device = provider.get_device(device_qrn)
        except Exception as exc:
            pytest.skip(f"Device {device_qrn} not available: {exc}")

        job = device.run(bell_kernel, shots=100)
        print(f"\n  QPU job submitted: {job.id}")

        # QPU jobs can take minutes to hours
        job.wait_for_final_state(timeout=3600, poll_interval=30)

        result = job.result()
        assert result.success, f"Job failed: {result.details}"

        counts = result.data.get_counts()
        print(f"  QPU counts: {counts}")

        # Basic sanity: got some results back
        assert len(counts) > 0
        total = sum(counts.values())
        assert total == 100

        # On real hardware, Bell should be dominated by "00" and "11"
        # but noise means other states may appear
        dominant = counts.get("00", 0) + counts.get("11", 0)
        assert dominant > 50, f"Bell state fidelity too low: {dominant}/100"

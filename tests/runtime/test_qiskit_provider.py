# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for QiskitProvider class

"""
from unittest.mock import Mock, patch

from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.providers.models import QasmBackendConfiguration
from qiskit_ibm_runtime import QiskitRuntimeService

from qbraid.runtime.qiskit import QiskitBackend, QiskitRuntimeProvider

from .fixtures import FakeService

# Skip tests if IBM account auth/creds not configured
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"


def test_qiskit_provider():
    """Test getting IBMQ provider using qiskit_ibm_provider package."""
    with patch("qbraid.runtime.qiskit.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = Mock(spec=QiskitRuntimeService)
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")
        assert isinstance(provider.runtime_service, QiskitRuntimeService)
        assert provider.token == "test_token"
        assert provider.channel == "test_channel"
        assert provider.runtime_service == mock_runtime_service.return_value


def test_get_service_backend():
    """Test getting a backend from the runtime service."""
    with patch("qbraid.runtime.qiskit.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = FakeService()
        assert isinstance(
            mock_runtime_service().backend("generic_backend_5q", instance=None), GenericBackendV2
        )


class TestQiskitDevice(GenericBackendV2):
    """A test Qiskit device."""

    def __init__(self, num_qubits):
        super().__init__(num_qubits)
        self._num_qubits = num_qubits
        self._instance = None

    def configuration(self):
        """Return the configuration of the backend."""
        return QasmBackendConfiguration(
            backend_name="fake_backend",
            backend_version="1.0",
            n_qubits=self._num_qubits,
            basis_gates=["u1", "u2", "u3", "cx"],
            gates=[],
            local=True,
            simulator=False,
            conditional=False,
            open_pulse=False,
            memory=False,
            max_shots=8192,
            coupling_map=None,
        )


def test_build_runtime_profile():
    """Test building runtime profile for Qiskit backend."""
    with patch("qbraid.runtime.qiskit.provider.QiskitRuntimeService") as mock_runtime_service:
        mock_runtime_service.return_value = FakeService()
        backend = TestQiskitDevice(5)
        provider = QiskitRuntimeProvider(token="test_token", channel="test_channel")
        profile = provider._build_runtime_profile(backend)
        assert profile._data["device_id"] == "generic_backend_5q"
        assert profile._data["device_type"] == "LOCAL_SIMULATOR"
        assert profile._data["num_qubits"] == 5
        assert profile._data["max_shots"] == 8192
        # basically testing get_device too
        qiskit_backend = QiskitBackend(profile, mock_runtime_service())
        assert isinstance(qiskit_backend, QiskitBackend)
        assert qiskit_backend.profile == profile

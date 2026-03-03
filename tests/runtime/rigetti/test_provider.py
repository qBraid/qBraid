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

# pylint: disable=redefined-outer-name

"""Unit tests for RigettiProvider."""

from unittest.mock import MagicMock, patch

import pyquil
import pytest

from qbraid.programs.experiment import ExperimentType
from qbraid.runtime import TargetProfile
from qbraid.runtime.rigetti import RigettiDevice, RigettiProvider

from .conftest import DEVICE_ID, DUMMY_CLIENT_ID, DUMMY_ISSUER, DUMMY_TOKEN


class TestRigettiProviderInit:
    """Tests for RigettiProvider.__init__ covering all env-var and client paths."""

    def test_explicit_client_bypasses_env_lookup(self, mock_qcs_client: MagicMock) -> None:
        """Test test explicit client bypasses env lookup."""
        with patch("os.getenv") as mock_getenv:
            provider = RigettiProvider(qcs_client=mock_qcs_client)
            mock_getenv.assert_not_called()
        assert provider._qcs_client is mock_qcs_client

    def test_missing_refresh_token_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test test missing refresh token raises value error."""
        monkeypatch.delenv("RIGETTI_REFRESH_TOKEN", raising=False)
        monkeypatch.setenv("RIGETTI_CLIENT_ID", DUMMY_CLIENT_ID)
        monkeypatch.setenv("RIGETTI_ISSUER", DUMMY_ISSUER)
        with pytest.raises(ValueError, match="refresh token"):
            RigettiProvider()

    def test_empty_refresh_token_raises_value_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test test empty refresh token raises value error."""
        monkeypatch.setenv("RIGETTI_REFRESH_TOKEN", "")
        monkeypatch.setenv("RIGETTI_CLIENT_ID", DUMMY_CLIENT_ID)
        monkeypatch.setenv("RIGETTI_ISSUER", DUMMY_ISSUER)
        with pytest.raises(ValueError, match="refresh token"):
            RigettiProvider()

    def test_init_with_custom_auth_server_when_client_id_and_issuer_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test test init with custom auth server when client id and issuer set."""
        monkeypatch.setenv("RIGETTI_REFRESH_TOKEN", DUMMY_TOKEN)
        monkeypatch.setenv("RIGETTI_CLIENT_ID", DUMMY_CLIENT_ID)
        monkeypatch.setenv("RIGETTI_ISSUER", DUMMY_ISSUER)

        with (
            patch("qbraid.runtime.rigetti.provider.AuthServer") as mock_auth_server_cls,
            patch("qbraid.runtime.rigetti.provider.OAuthSession"),
            patch("qbraid.runtime.rigetti.provider.RefreshToken"),
            patch("qbraid.runtime.rigetti.provider.QCSClient") as mock_qcs_client_cls,
        ):
            mock_auth_server_cls.return_value = MagicMock(name="CustomAuthServer")
            mock_qcs_client_cls.return_value = MagicMock(name="QCSClient")

            provider = RigettiProvider()

            mock_auth_server_cls.assert_called_once_with(
                client_id=DUMMY_CLIENT_ID, issuer=DUMMY_ISSUER
            )
            mock_auth_server_cls.default.assert_not_called()
            assert isinstance(provider, RigettiProvider)

    def test_init_falls_back_to_default_auth_server_when_client_id_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test test init falls back to default auth server when client id missing."""
        monkeypatch.setenv("RIGETTI_REFRESH_TOKEN", DUMMY_TOKEN)
        monkeypatch.delenv("RIGETTI_CLIENT_ID", raising=False)
        monkeypatch.setenv("RIGETTI_ISSUER", DUMMY_ISSUER)

        with (
            patch("qbraid.runtime.rigetti.provider.AuthServer") as mock_auth_server_cls,
            patch("qbraid.runtime.rigetti.provider.OAuthSession"),
            patch("qbraid.runtime.rigetti.provider.RefreshToken"),
            patch("qbraid.runtime.rigetti.provider.QCSClient") as mock_qcs_client_cls,
        ):
            mock_auth_server_cls.default.return_value = MagicMock(name="DefaultAuthServer")
            mock_qcs_client_cls.return_value = MagicMock(name="QCSClient")

            RigettiProvider()

            mock_auth_server_cls.default.assert_called_once()
            mock_auth_server_cls.assert_not_called()

    def test_init_falls_back_to_default_auth_server_when_issuer_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test test init falls back to default auth server when issuer missing."""
        monkeypatch.setenv("RIGETTI_REFRESH_TOKEN", DUMMY_TOKEN)
        monkeypatch.setenv("RIGETTI_CLIENT_ID", DUMMY_CLIENT_ID)
        monkeypatch.delenv("RIGETTI_ISSUER", raising=False)

        with (
            patch("qbraid.runtime.rigetti.provider.AuthServer") as mock_auth_server_cls,
            patch("qbraid.runtime.rigetti.provider.OAuthSession"),
            patch("qbraid.runtime.rigetti.provider.RefreshToken"),
            patch("qbraid.runtime.rigetti.provider.QCSClient") as mock_qcs_client_cls,
        ):
            mock_auth_server_cls.default.return_value = MagicMock(name="DefaultAuthServer")
            mock_qcs_client_cls.return_value = MagicMock(name="QCSClient")

            RigettiProvider()

            mock_auth_server_cls.default.assert_called_once()
            mock_auth_server_cls.assert_not_called()

    def test_init_falls_back_to_default_auth_server_when_both_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test test init falls back to default auth server when both missing."""
        monkeypatch.setenv("RIGETTI_REFRESH_TOKEN", DUMMY_TOKEN)
        monkeypatch.delenv("RIGETTI_CLIENT_ID", raising=False)
        monkeypatch.delenv("RIGETTI_ISSUER", raising=False)

        with (
            patch("qbraid.runtime.rigetti.provider.AuthServer") as mock_auth_server_cls,
            patch("qbraid.runtime.rigetti.provider.OAuthSession"),
            patch("qbraid.runtime.rigetti.provider.RefreshToken"),
            patch("qbraid.runtime.rigetti.provider.QCSClient") as mock_qcs_client_cls,
        ):
            mock_auth_server_cls.default.return_value = MagicMock(name="DefaultAuthServer")
            mock_qcs_client_cls.return_value = MagicMock(name="QCSClient")

            provider = RigettiProvider()

            mock_auth_server_cls.default.assert_called_once()
            assert isinstance(provider, RigettiProvider)

    def test_qcs_client_constructed_with_oauth_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test test qcs client constructed with oauth session."""
        monkeypatch.setenv("RIGETTI_REFRESH_TOKEN", DUMMY_TOKEN)
        monkeypatch.delenv("RIGETTI_CLIENT_ID", raising=False)
        monkeypatch.delenv("RIGETTI_ISSUER", raising=False)

        with (
            patch("qbraid.runtime.rigetti.provider.AuthServer") as mock_auth_server_cls,
            patch("qbraid.runtime.rigetti.provider.OAuthSession") as mock_oauth_session_cls,
            patch("qbraid.runtime.rigetti.provider.RefreshToken") as mock_refresh_token_cls,
            patch("qbraid.runtime.rigetti.provider.QCSClient") as mock_qcs_client_cls,
        ):
            fake_auth_server = MagicMock(name="DefaultAuthServer")
            fake_oauth_session = MagicMock(name="OAuthSession")
            fake_refresh_token = MagicMock(name="RefreshToken")
            fake_client = MagicMock(name="QCSClient")

            mock_auth_server_cls.default.return_value = fake_auth_server
            mock_refresh_token_cls.return_value = fake_refresh_token
            mock_oauth_session_cls.return_value = fake_oauth_session
            mock_qcs_client_cls.return_value = fake_client

            provider = RigettiProvider()

            mock_refresh_token_cls.assert_called_once_with(refresh_token=DUMMY_TOKEN)
            mock_oauth_session_cls.assert_called_once_with(fake_refresh_token, fake_auth_server)
            mock_qcs_client_cls.assert_called_once_with(oauth_session=fake_oauth_session)

            assert provider._qcs_client is fake_client


class TestRigettiProviderBuildProfile:
    """Tests for RigettiProvider._build_profile."""

    def test_build_profile_returns_target_profile(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test build profile returns target profile."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ):
            profile = provider._build_profile(DEVICE_ID)

        assert isinstance(profile, TargetProfile)
        assert profile.device_id == DEVICE_ID
        assert profile.simulator is False
        assert profile.num_qubits == len(mock_isa_response.architecture.nodes)
        assert profile.provider_name == "rigetti"
        assert profile.experiment_type == ExperimentType.GATE_MODEL

    def test_build_profile_calls_get_isa_with_correct_args(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test build profile calls get isa with correct args."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ) as mock_get_isa:
            provider._build_profile(DEVICE_ID)

        mock_get_isa.assert_called_once_with(
            quantum_processor_id=DEVICE_ID,
            client=mock_qcs_client,
        )

    def test_build_profile_num_qubits_reflects_node_count(self, mock_qcs_client: MagicMock) -> None:
        """Test test build profile num qubits reflects node count."""
        node_count = 7
        isa = MagicMock()
        isa.architecture.nodes = [MagicMock(node_id=i) for i in range(node_count)]

        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
            return_value=isa,
        ):
            profile = provider._build_profile(DEVICE_ID)

        assert profile.num_qubits == node_count

    def test_build_profile_program_spec_is_pyquil_program(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test build profile program spec is pyquil program."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ):
            profile = provider._build_profile(DEVICE_ID)

        assert profile.program_spec is not None
        assert profile.program_spec.program_type is pyquil.Program


class TestRigettiProviderGetDevices:
    """Tests for RigettiProvider.get_devices."""

    def test_get_devices_returns_list_of_rigetti_devices(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test get devices returns list of rigetti devices."""
        processor_ids = ["Ankaa-3", "Aspen-M-3"]
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(
                "qbraid.runtime.rigetti.provider.list_quantum_processors",
                return_value=processor_ids,
            ),
            patch(
                "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
                return_value=mock_isa_response,
            ),
        ):
            devices = provider.get_devices()

        assert isinstance(devices, list)
        assert len(devices) == len(processor_ids)
        for device in devices:
            assert isinstance(device, RigettiDevice)

    def test_get_devices_calls_list_quantum_processors_with_client(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test get devices calls list quantum processors with client."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(
                "qbraid.runtime.rigetti.provider.list_quantum_processors",
                return_value=["Ankaa-3"],
            ) as mock_list,
            patch(
                "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
                return_value=mock_isa_response,
            ),
        ):
            provider.get_devices()

        mock_list.assert_called_once_with(client=mock_qcs_client)

    def test_get_devices_returns_empty_list_when_no_processors(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """Test test get devices returns empty list when no processors."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.provider.list_quantum_processors",
            return_value=[],
        ):
            devices = provider.get_devices()

        assert not devices

    def test_get_devices_builds_profile_for_each_processor(
        self, mock_qcs_client: MagicMock, qpu_profile: TargetProfile
    ) -> None:
        """Test test get devices builds profile for each processor."""
        processor_ids = ["Ankaa-3", "Aspen-M-3", "Ankaa-9Q-1"]
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(
                "qbraid.runtime.rigetti.provider.list_quantum_processors",
                return_value=processor_ids,
            ),
            patch.object(provider, "_build_profile", return_value=qpu_profile) as mock_build,
        ):
            provider.get_devices()

        assert mock_build.call_count == len(processor_ids)
        mock_build.assert_any_call(quantum_processor_id=processor_ids[0])
        mock_build.assert_any_call(quantum_processor_id=processor_ids[1])

    def test_get_devices_devices_share_same_client(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test get devices devices share same client."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(
                "qbraid.runtime.rigetti.provider.list_quantum_processors",
                return_value=["Ankaa-3", "Aspen-M-3"],
            ),
            patch(
                "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
                return_value=mock_isa_response,
            ),
        ):
            devices = provider.get_devices()

        for device in devices:
            assert device._qcs_client is mock_qcs_client


class TestRigettiProviderGetDevice:
    """Tests for RigettiProvider.get_device."""

    def test_get_device_returns_rigetti_device(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test get device returns rigetti device."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ):
            device = provider.get_device(DEVICE_ID)

        assert isinstance(device, RigettiDevice)

    def test_get_device_profile_has_correct_device_id(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test get device profile has correct device id."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ):
            device = provider.get_device(DEVICE_ID)

        assert device.profile.device_id == DEVICE_ID

    def test_get_device_device_carries_correct_client(
        self, mock_qcs_client: MagicMock, mock_isa_response: MagicMock
    ) -> None:
        """Test test get device device carries correct client."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch(
            "qbraid.runtime.rigetti.provider.get_instruction_set_architecture",
            return_value=mock_isa_response,
        ):
            device = provider.get_device(DEVICE_ID)

        assert device._qcs_client is mock_qcs_client

    def test_get_device_calls_build_profile_once(
        self, mock_qcs_client: MagicMock, qpu_profile: TargetProfile
    ) -> None:
        """Test test get device calls build profile once."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch.object(provider, "_build_profile", return_value=qpu_profile) as mock_build:
            provider.get_device(DEVICE_ID)

        mock_build.assert_called_once_with(quantum_processor_id=DEVICE_ID)

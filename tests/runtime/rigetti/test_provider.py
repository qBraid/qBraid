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

# pylint: disable=redefined-outer-name,too-many-lines,import-outside-toplevel,possibly-used-before-assignment

"""Unit tests for RigettiProvider."""

from __future__ import annotations

import importlib.util
from unittest.mock import MagicMock, patch

import pytest

from qbraid.programs.experiment import ExperimentType
from qbraid.runtime import TargetProfile

from .conftest import DEVICE_ID, DUMMY_CLIENT_ID, DUMMY_ISSUER, DUMMY_TOKEN

pyquil_found = importlib.util.find_spec("pyquil") is not None
pytestmark = pytest.mark.skipif(not pyquil_found, reason="pyquil not installed")

if pyquil_found:
    from qbraid.runtime.rigetti import RigettiDevice, RigettiProvider
else:
    RigettiDevice = None
    RigettiProvider = None


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
            mock_qcs_client_cls.assert_called_once_with(
                oauth_session=fake_oauth_session,
                grpc_api_url="https://grpc.qcs.rigetti.com",
                quilc_url="tcp://127.0.0.1:5555",
                qvm_url="http://127.0.0.1:5000",
            )

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
        # pylint: disable=import-outside-toplevel
        import pyquil

        # pylint: enable=import-outside-toplevel
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


# ---------------------------------------------------------------------------
# New test classes for methods added in the setup / process-management layer
# ---------------------------------------------------------------------------

if pyquil_found:
    from subprocess import TimeoutExpired

    from qbraid.runtime.rigetti.provider import RigettiProviderError

_PROVIDER_MODULE = "qbraid.runtime.rigetti.provider"


class TestBuildQcsClient:
    """Tests for the static method RigettiProvider._build_qcs_client."""

    def test_build_qcs_client_uses_default_auth_server_when_no_client_id(self) -> None:
        """When client_id is None, AuthServer.default() should be used."""
        with (
            patch(f"{_PROVIDER_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_PROVIDER_MODULE}.OAuthSession") as mock_oauth_cls,
            patch(f"{_PROVIDER_MODULE}.RefreshToken") as mock_rt_cls,
            patch(f"{_PROVIDER_MODULE}.QCSClient") as mock_qcs_cls,
        ):
            fake_auth = MagicMock(name="DefaultAuthServer")
            mock_auth_cls.default.return_value = fake_auth
            mock_rt_cls.return_value = MagicMock(name="RefreshToken")
            mock_oauth_cls.return_value = MagicMock(name="OAuthSession")
            mock_qcs_cls.return_value = MagicMock(name="QCSClient")

            RigettiProvider._build_qcs_client(refresh_token=DUMMY_TOKEN)

            mock_auth_cls.default.assert_called_once()
            mock_auth_cls.assert_not_called()

    def test_build_qcs_client_uses_default_auth_server_when_no_issuer(self) -> None:
        """When issuer is None, AuthServer.default() should be used."""
        with (
            patch(f"{_PROVIDER_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_PROVIDER_MODULE}.OAuthSession"),
            patch(f"{_PROVIDER_MODULE}.RefreshToken"),
            patch(f"{_PROVIDER_MODULE}.QCSClient"),
        ):
            mock_auth_cls.default.return_value = MagicMock()

            RigettiProvider._build_qcs_client(
                refresh_token=DUMMY_TOKEN,
                client_id=DUMMY_CLIENT_ID,
                issuer=None,
            )

            mock_auth_cls.default.assert_called_once()
            mock_auth_cls.assert_not_called()

    def test_build_qcs_client_uses_custom_auth_server_when_both_provided(self) -> None:
        """When both client_id and issuer are given, AuthServer(client_id, issuer) is used."""
        with (
            patch(f"{_PROVIDER_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_PROVIDER_MODULE}.OAuthSession"),
            patch(f"{_PROVIDER_MODULE}.RefreshToken"),
            patch(f"{_PROVIDER_MODULE}.QCSClient"),
        ):
            mock_auth_cls.return_value = MagicMock(name="CustomAuth")

            RigettiProvider._build_qcs_client(
                refresh_token=DUMMY_TOKEN,
                client_id=DUMMY_CLIENT_ID,
                issuer=DUMMY_ISSUER,
            )

            mock_auth_cls.assert_called_once_with(client_id=DUMMY_CLIENT_ID, issuer=DUMMY_ISSUER)
            mock_auth_cls.default.assert_not_called()

    def test_build_qcs_client_passes_url_kwargs(self) -> None:
        """URL parameters should be forwarded to QCSClient constructor."""
        with (
            patch(f"{_PROVIDER_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_PROVIDER_MODULE}.OAuthSession") as mock_oauth_cls,
            patch(f"{_PROVIDER_MODULE}.RefreshToken"),
            patch(f"{_PROVIDER_MODULE}.QCSClient") as mock_qcs_cls,
        ):
            mock_auth_cls.default.return_value = MagicMock()
            fake_session = MagicMock(name="OAuthSession")
            mock_oauth_cls.return_value = fake_session

            grpc = "https://custom-grpc:443"
            quilc = "tcp://custom-quilc:5555"
            qvm = "http://custom-qvm:5000"

            RigettiProvider._build_qcs_client(
                refresh_token=DUMMY_TOKEN,
                grpc_api_url=grpc,
                quilc_url=quilc,
                qvm_url=qvm,
            )

            mock_qcs_cls.assert_called_once_with(
                oauth_session=fake_session,
                grpc_api_url=grpc,
                quilc_url=quilc,
                qvm_url=qvm,
            )

    def test_build_qcs_client_omits_url_kwargs_when_none(self) -> None:
        """When URL params are None they should not appear in QCSClient kwargs."""
        with (
            patch(f"{_PROVIDER_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_PROVIDER_MODULE}.OAuthSession") as mock_oauth_cls,
            patch(f"{_PROVIDER_MODULE}.RefreshToken"),
            patch(f"{_PROVIDER_MODULE}.QCSClient") as mock_qcs_cls,
        ):
            mock_auth_cls.default.return_value = MagicMock()
            fake_session = MagicMock(name="OAuthSession")
            mock_oauth_cls.return_value = fake_session

            RigettiProvider._build_qcs_client(
                refresh_token=DUMMY_TOKEN,
                grpc_api_url=None,
                quilc_url=None,
                qvm_url=None,
            )

            mock_qcs_cls.assert_called_once_with(oauth_session=fake_session)


class TestIsPortInUse:
    """Tests for the static method RigettiProvider._is_port_in_use."""

    def test_returns_true_when_port_is_open(self) -> None:
        """A successful connect_ex (returns 0) means the port is in use."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with patch("qbraid.runtime.rigetti.provider.socket.socket", return_value=mock_sock):
            assert RigettiProvider._is_port_in_use(5555) is True

        mock_sock.connect_ex.assert_called_once_with(("127.0.0.1", 5555))

    def test_returns_false_when_port_is_closed(self) -> None:
        """A non-zero connect_ex means the port is not in use."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111  # ECONNREFUSED
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with patch("qbraid.runtime.rigetti.provider.socket.socket", return_value=mock_sock):
            assert RigettiProvider._is_port_in_use(5555) is False

    def test_uses_custom_host(self) -> None:
        """The host parameter should be forwarded to connect_ex."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with patch("qbraid.runtime.rigetti.provider.socket.socket", return_value=mock_sock):
            RigettiProvider._is_port_in_use(9999, host="10.0.0.1")

        mock_sock.connect_ex.assert_called_once_with(("10.0.0.1", 9999))


class TestFindBinary:
    """Tests for the static method RigettiProvider._find_binary."""

    def test_returns_path_from_shutil_which(self) -> None:
        """When shutil.which finds the binary, its path is returned."""
        with patch("qbraid.runtime.rigetti.provider.shutil.which", return_value="/usr/bin/quilc"):
            result = RigettiProvider._find_binary("quilc")

        from pathlib import Path

        assert result == Path("/usr/bin/quilc")

    def test_falls_back_to_qbraid_bin_dir(self) -> None:
        """When shutil.which returns None, check ~/.qbraid/rigetti/bin/."""
        from pathlib import Path

        fallback_path = Path.home() / ".qbraid" / "rigetti" / "bin" / "quilc"

        with (
            patch("qbraid.runtime.rigetti.provider.shutil.which", return_value=None),
            patch.object(Path, "is_file", return_value=True),
            patch("qbraid.runtime.rigetti.provider.os.access", return_value=True),
        ):
            result = RigettiProvider._find_binary("quilc")

        assert result == fallback_path

    def test_returns_none_when_not_found(self) -> None:
        """When neither shutil.which nor the fallback finds the binary, return None."""
        from pathlib import Path

        with (
            patch("qbraid.runtime.rigetti.provider.shutil.which", return_value=None),
            patch.object(Path, "is_file", return_value=False),
        ):
            result = RigettiProvider._find_binary("quilc")

        assert result is None

    def test_returns_none_when_fallback_not_executable(self) -> None:
        """When the fallback file exists but is not executable, return None."""
        from pathlib import Path

        with (
            patch("qbraid.runtime.rigetti.provider.shutil.which", return_value=None),
            patch.object(Path, "is_file", return_value=True),
            patch("qbraid.runtime.rigetti.provider.os.access", return_value=False),
        ):
            result = RigettiProvider._find_binary("quilc")

        assert result is None


class TestWaitForPort:
    """Tests for the static method RigettiProvider._wait_for_port."""

    def test_returns_immediately_when_port_is_open(self) -> None:
        """If the port is already accepting connections, return immediately."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with (
            patch("qbraid.runtime.rigetti.provider.socket.socket", return_value=mock_sock),
            patch("qbraid.runtime.rigetti.provider.time.monotonic", side_effect=[0.0, 0.1]),
        ):
            # Should not raise
            RigettiProvider._wait_for_port(5555, timeout=5.0)

    def test_raises_on_timeout(self) -> None:
        """If the port never opens, raise RigettiProviderError."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111  # always refused
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        # Simulate time progressing past the deadline
        with (
            patch("qbraid.runtime.rigetti.provider.socket.socket", return_value=mock_sock),
            patch(
                "qbraid.runtime.rigetti.provider.time.monotonic",
                side_effect=[0.0, 0.5, 100.0],
            ),
            patch("qbraid.runtime.rigetti.provider.time.sleep"),
            pytest.raises(RigettiProviderError, match="Timed out waiting for port"),
        ):
            RigettiProvider._wait_for_port(5555, timeout=5.0)

    def test_retries_until_port_opens(self) -> None:
        """Should retry polling until the port starts accepting connections."""
        mock_sock = MagicMock()
        # First two checks fail, third succeeds
        mock_sock.connect_ex.side_effect = [111, 111, 0]
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with (
            patch("qbraid.runtime.rigetti.provider.socket.socket", return_value=mock_sock),
            patch(
                "qbraid.runtime.rigetti.provider.time.monotonic",
                side_effect=[0.0, 0.5, 1.0, 1.5, 2.0],
            ),
            patch("qbraid.runtime.rigetti.provider.time.sleep") as mock_sleep,
        ):
            RigettiProvider._wait_for_port(5555, timeout=10.0)

        assert mock_sock.connect_ex.call_count == 3
        assert mock_sleep.call_count == 2


class TestStartQuilc:
    """Tests for RigettiProvider._start_quilc."""

    def test_start_quilc_spawns_popen_and_waits(self, mock_qcs_client: MagicMock) -> None:
        """_start_quilc should invoke Popen and then wait for the port."""
        from pathlib import Path

        provider = RigettiProvider(qcs_client=mock_qcs_client)
        binary = Path("/usr/local/bin/quilc")
        fake_proc = MagicMock(name="quilc_process", pid=12345)

        with (
            patch(f"{_PROVIDER_MODULE}.Popen", return_value=fake_proc) as mock_popen,
            patch.object(provider, "_wait_for_port") as mock_wait,
        ):
            provider._start_quilc(binary)

        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == [str(binary), "-S"]
        mock_wait.assert_called_once_with(5555)
        assert provider._quilc_process is fake_proc


class TestStartQvm:
    """Tests for RigettiProvider._start_qvm."""

    def test_start_qvm_spawns_popen_and_waits(self, mock_qcs_client: MagicMock) -> None:
        """_start_qvm should invoke Popen and then wait for the port."""
        from pathlib import Path

        provider = RigettiProvider(qcs_client=mock_qcs_client)
        binary = Path("/usr/local/bin/qvm")
        fake_proc = MagicMock(name="qvm_process", pid=54321)

        with (
            patch(f"{_PROVIDER_MODULE}.Popen", return_value=fake_proc) as mock_popen,
            patch.object(provider, "_wait_for_port") as mock_wait,
        ):
            provider._start_qvm(binary)

        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == [str(binary), "-S"]
        mock_wait.assert_called_once_with(5000)
        assert provider._qvm_process is fake_proc


class TestCleanup:
    """Tests for RigettiProvider._cleanup."""

    def test_cleanup_does_nothing_when_no_processes_owned(self, mock_qcs_client: MagicMock) -> None:
        """When _quilc_process and _qvm_process are None, nothing is terminated."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)
        assert provider._quilc_process is None
        assert provider._qvm_process is None

        # Should not raise
        provider._cleanup()

    def test_cleanup_terminates_owned_quilc_process(self, mock_qcs_client: MagicMock) -> None:
        """A started quilc process should be terminated and waited on."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)
        mock_proc = MagicMock(pid=111)
        provider._quilc_process = mock_proc

        provider._cleanup()

        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once_with(timeout=5)
        assert provider._quilc_process is None

    def test_cleanup_terminates_owned_qvm_process(self, mock_qcs_client: MagicMock) -> None:
        """A started qvm process should be terminated and waited on."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)
        mock_proc = MagicMock(pid=222)
        provider._qvm_process = mock_proc

        provider._cleanup()

        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once_with(timeout=5)
        assert provider._qvm_process is None

    def test_cleanup_kills_process_on_timeout(self, mock_qcs_client: MagicMock) -> None:
        """When wait() times out, SIGKILL should be sent via kill()."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)
        mock_proc = MagicMock(pid=333)
        mock_proc.wait.side_effect = TimeoutExpired(cmd="quilc", timeout=5)
        provider._quilc_process = mock_proc

        provider._cleanup()

        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
        assert provider._quilc_process is None

    def test_cleanup_handles_both_processes(self, mock_qcs_client: MagicMock) -> None:
        """When both processes are owned, both should be terminated."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)
        quilc_proc = MagicMock(pid=444)
        qvm_proc = MagicMock(pid=555)
        provider._quilc_process = quilc_proc
        provider._qvm_process = qvm_proc

        provider._cleanup()

        quilc_proc.terminate.assert_called_once()
        qvm_proc.terminate.assert_called_once()
        assert provider._quilc_process is None
        assert provider._qvm_process is None


class TestSignalHandler:
    """Tests for RigettiProvider._signal_handler."""

    def test_signal_handler_sigint_raises_keyboard_interrupt(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """SIGINT should trigger _cleanup and raise KeyboardInterrupt."""
        import signal as sig

        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch.object(provider, "_cleanup") as mock_cleanup,
            pytest.raises(KeyboardInterrupt),
        ):
            provider._signal_handler(sig.SIGINT, None)

        mock_cleanup.assert_called_once()

    def test_signal_handler_sigterm_raises_system_exit(self, mock_qcs_client: MagicMock) -> None:
        """SIGTERM should trigger _cleanup and raise SystemExit."""
        import signal as sig

        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch.object(provider, "_cleanup") as mock_cleanup,
            pytest.raises(SystemExit),
        ):
            provider._signal_handler(sig.SIGTERM, None)

        mock_cleanup.assert_called_once()


class TestRegisterCleanup:
    """Tests for RigettiProvider._register_cleanup."""

    def test_register_cleanup_registers_atexit_and_signals(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """First call should register atexit handler and signal handlers."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)
        assert provider._cleanup_registered is False

        with (
            patch("qbraid.runtime.rigetti.provider.atexit.register") as mock_atexit,
            patch("qbraid.runtime.rigetti.provider.signal.getsignal") as mock_getsig,
            patch("qbraid.runtime.rigetti.provider.signal.signal") as mock_signal,
        ):
            mock_getsig.return_value = MagicMock()
            provider._register_cleanup()

        mock_atexit.assert_called_once_with(provider._cleanup)
        assert mock_signal.call_count == 2
        assert provider._cleanup_registered is True

    def test_register_cleanup_only_registers_once(self, mock_qcs_client: MagicMock) -> None:
        """Calling _register_cleanup twice should only register handlers once."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch("qbraid.runtime.rigetti.provider.atexit.register") as mock_atexit,
            patch("qbraid.runtime.rigetti.provider.signal.getsignal"),
            patch("qbraid.runtime.rigetti.provider.signal.signal"),
        ):
            provider._register_cleanup()
            provider._register_cleanup()

        mock_atexit.assert_called_once()


class TestDownloadForestSdk:
    """Tests for the static method RigettiProvider._download_forest_sdk."""

    def test_download_forest_sdk_raises_rigetti_provider_error(self) -> None:
        """Should raise RigettiProviderError with installation instructions."""
        with pytest.raises(RigettiProviderError, match="quilc binary not found"):
            RigettiProvider._download_forest_sdk()


class TestSetup:
    """Tests for RigettiProvider.setup — the main orchestration method."""

    def test_setup_with_explicit_credentials_rebuilds_client(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """Passing refresh_token explicitly should rebuild _qcs_client."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)
        fake_new_client = MagicMock(name="NewQCSClient")

        with (
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=fake_new_client,
            ) as mock_build,
            patch.object(RigettiProvider, "_is_port_in_use", return_value=True),
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(
                refresh_token=DUMMY_TOKEN,
                client_id=DUMMY_CLIENT_ID,
                issuer=DUMMY_ISSUER,
                start_quilc=False,
                start_qvm=False,
                interactive=False,
            )

        mock_build.assert_called_once()
        assert provider._qcs_client is fake_new_client

    def test_setup_interactive_prompts_for_missing_token(
        self, mock_qcs_client: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When interactive=True and token is missing, input() should be called."""
        monkeypatch.delenv("RIGETTI_REFRESH_TOKEN", raising=False)
        monkeypatch.delenv("RIGETTI_CLIENT_ID", raising=False)
        monkeypatch.delenv("RIGETTI_ISSUER", raising=False)
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch("builtins.input", side_effect=["my-token", "", ""]) as mock_input,
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(RigettiProvider, "_is_port_in_use", return_value=True),
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(interactive=True, start_quilc=False, start_qvm=False)

        # input() should have been called at least once for the token
        assert mock_input.call_count >= 1
        first_prompt = mock_input.call_args_list[0][0][0]
        assert "refresh token" in first_prompt.lower()

    def test_setup_non_interactive_raises_without_token(
        self, mock_qcs_client: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When interactive=False and no token available, raise ValueError."""
        monkeypatch.delenv("RIGETTI_REFRESH_TOKEN", raising=False)
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with pytest.raises(ValueError, match="refresh token"):
            provider.setup(interactive=False, start_quilc=False, start_qvm=False)

    def test_setup_skips_quilc_when_endpoint_provided(self, mock_qcs_client: MagicMock) -> None:
        """When quilc_endpoint is given, no local quilc process should be started."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(RigettiProvider, "_is_port_in_use") as mock_port,
            patch.object(provider, "_start_quilc") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(
                refresh_token=DUMMY_TOKEN,
                quilc_endpoint="tcp://remote:5555",
                start_quilc=True,
                start_qvm=False,
                interactive=False,
            )

        mock_port.assert_not_called()
        mock_start.assert_not_called()

    def test_setup_skips_quilc_when_port_already_in_use(self, mock_qcs_client: MagicMock) -> None:
        """When the quilc port is already in use, no Popen should be called."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(RigettiProvider, "_is_port_in_use", return_value=True),
            patch.object(provider, "_start_quilc") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(
                refresh_token=DUMMY_TOKEN,
                start_quilc=True,
                start_qvm=False,
                interactive=False,
            )

        mock_start.assert_not_called()

    def test_setup_starts_quilc_when_port_free_and_binary_found(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """When port is free and binary is found, _start_quilc should be called."""
        from pathlib import Path

        provider = RigettiProvider(qcs_client=mock_qcs_client)
        fake_binary = Path("/usr/local/bin/quilc")

        with (
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(RigettiProvider, "_is_port_in_use", return_value=False),
            patch.object(RigettiProvider, "_find_binary", return_value=fake_binary),
            patch.object(provider, "_start_quilc") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(
                refresh_token=DUMMY_TOKEN,
                start_quilc=True,
                start_qvm=False,
                interactive=False,
            )

        mock_start.assert_called_once_with(fake_binary)

    def test_setup_calls_download_forest_sdk_when_binary_missing(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """When quilc binary is not found, _download_forest_sdk should be called."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(RigettiProvider, "_is_port_in_use", return_value=False),
            patch.object(RigettiProvider, "_find_binary", return_value=None),
            patch.object(
                RigettiProvider,
                "_download_forest_sdk",
                side_effect=RigettiProviderError("not found"),
            ) as mock_download,
            patch.object(provider, "_register_cleanup"),
        ):
            with pytest.raises(RigettiProviderError):
                provider.setup(
                    refresh_token=DUMMY_TOKEN,
                    start_quilc=True,
                    start_qvm=False,
                    interactive=False,
                )

        mock_download.assert_called_once()

    def test_setup_skips_qvm_when_endpoint_provided(self, mock_qcs_client: MagicMock) -> None:
        """When qvm_endpoint is given, no local qvm process should be started."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(provider, "_start_qvm") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(
                refresh_token=DUMMY_TOKEN,
                qvm_endpoint="http://remote:5000",
                start_quilc=False,
                start_qvm=True,
                interactive=False,
            )

        mock_start.assert_not_called()

    def test_setup_starts_qvm_when_port_free_and_binary_found(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """When qvm port is free and binary is found, _start_qvm should be called."""
        from pathlib import Path

        provider = RigettiProvider(qcs_client=mock_qcs_client)
        fake_binary = Path("/usr/local/bin/qvm")

        with (
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(RigettiProvider, "_is_port_in_use", return_value=False),
            patch.object(RigettiProvider, "_find_binary", return_value=fake_binary),
            patch.object(provider, "_start_qvm") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(
                refresh_token=DUMMY_TOKEN,
                start_quilc=False,
                start_qvm=True,
                interactive=False,
            )

        mock_start.assert_called_once_with(fake_binary)

    def test_setup_registers_cleanup(self, mock_qcs_client: MagicMock) -> None:
        """setup() should always call _register_cleanup at the end."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(provider, "_register_cleanup") as mock_register,
        ):
            provider.setup(
                refresh_token=DUMMY_TOKEN,
                start_quilc=False,
                start_qvm=False,
                interactive=False,
            )

        mock_register.assert_called_once()

    def test_setup_interactive_prompts_for_client_id_and_issuer(
        self, mock_qcs_client: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When interactive=True and client_id/issuer are missing, prompt for them."""
        monkeypatch.delenv("RIGETTI_REFRESH_TOKEN", raising=False)
        monkeypatch.delenv("RIGETTI_CLIENT_ID", raising=False)
        monkeypatch.delenv("RIGETTI_ISSUER", raising=False)
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(
                "builtins.input",
                side_effect=[DUMMY_TOKEN, DUMMY_CLIENT_ID, DUMMY_ISSUER],
            ) as mock_input,
            patch.object(
                RigettiProvider,
                "_build_qcs_client",
                return_value=MagicMock(),
            ),
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(interactive=True, start_quilc=False, start_qvm=False)

        # Three prompts: token, client_id, issuer
        assert mock_input.call_count == 3

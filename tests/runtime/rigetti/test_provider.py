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

# pylint: disable=redefined-outer-name,import-outside-toplevel,possibly-used-before-assignment

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
    from qbraid.runtime.rigetti.setup import RigettiProviderError
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
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_server_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession"),
            patch(f"{_SETUP_MODULE}.RefreshToken"),
            patch(f"{_SETUP_MODULE}.QCSClient") as mock_qcs_client_cls,
            patch.object(RigettiProvider, "_build_execution_options", return_value=MagicMock()),
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
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_server_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession"),
            patch(f"{_SETUP_MODULE}.RefreshToken"),
            patch(f"{_SETUP_MODULE}.QCSClient") as mock_qcs_client_cls,
            patch.object(RigettiProvider, "_build_execution_options", return_value=MagicMock()),
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
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_server_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession"),
            patch(f"{_SETUP_MODULE}.RefreshToken"),
            patch(f"{_SETUP_MODULE}.QCSClient") as mock_qcs_client_cls,
            patch.object(RigettiProvider, "_build_execution_options", return_value=MagicMock()),
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
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_server_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession"),
            patch(f"{_SETUP_MODULE}.RefreshToken"),
            patch(f"{_SETUP_MODULE}.QCSClient") as mock_qcs_client_cls,
            patch.object(RigettiProvider, "_build_execution_options", return_value=MagicMock()),
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
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_server_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession") as mock_oauth_session_cls,
            patch(f"{_SETUP_MODULE}.RefreshToken") as mock_refresh_token_cls,
            patch(f"{_SETUP_MODULE}.QCSClient") as mock_qcs_client_cls,
            patch.object(RigettiProvider, "_build_execution_options", return_value=MagicMock()),
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
            assert device.client is mock_qcs_client


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

        assert device.client is mock_qcs_client

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

_PROVIDER_MODULE = "qbraid.runtime.rigetti.provider"
_SETUP_MODULE = "qbraid.runtime.rigetti.setup"


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
            patch(f"{_PROVIDER_MODULE}.wait_for_port") as mock_wait,
        ):
            provider._start_quilc(binary)

        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == [str(binary), "-P", "-S", "-p", "5555"]
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
            patch(f"{_PROVIDER_MODULE}.wait_for_port") as mock_wait,
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


class TestSetup:
    """Tests for RigettiProvider.setup -- local quilc/qvm process management.

    Credentials and the QCSClient are bootstrapped once in __init__; setup()
    is purely concerned with the optional lifecycle of the local quilc and
    qvm helper binaries plus cleanup-handler registration.
    """

    def test_setup_does_not_rebuild_qcs_client(self, mock_qcs_client: MagicMock) -> None:
        """setup() must NOT call build_qcs_client; the client is set in __init__."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(f"{_PROVIDER_MODULE}.build_qcs_client") as mock_build,
            patch(f"{_PROVIDER_MODULE}.is_port_in_use", return_value=True),
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(start_quilc=False, start_qvm=False)

        mock_build.assert_not_called()
        assert provider._qcs_client is mock_qcs_client

    def test_setup_skips_quilc_when_endpoint_provided(self, mock_qcs_client: MagicMock) -> None:
        """When quilc_endpoint is given, no local quilc process should be started."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(f"{_PROVIDER_MODULE}.is_port_in_use") as mock_port,
            patch.object(provider, "_start_quilc") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(
                quilc_endpoint="tcp://remote:5555",
                start_quilc=True,
                start_qvm=False,
            )

        mock_port.assert_not_called()
        mock_start.assert_not_called()

    def test_setup_skips_quilc_when_port_already_in_use(self, mock_qcs_client: MagicMock) -> None:
        """When the quilc port is already in use, no Popen should be called."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(f"{_PROVIDER_MODULE}.is_port_in_use", return_value=True),
            patch.object(provider, "_start_quilc") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(start_quilc=True, start_qvm=False)

        mock_start.assert_not_called()

    def test_setup_starts_quilc_when_port_free_and_binary_found(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """When port is free and binary is found, _start_quilc should be called."""
        from pathlib import Path

        provider = RigettiProvider(qcs_client=mock_qcs_client)
        fake_binary = Path("/usr/local/bin/quilc")

        with (
            patch(f"{_PROVIDER_MODULE}.is_port_in_use", return_value=False),
            patch(f"{_PROVIDER_MODULE}.find_binary", return_value=fake_binary),
            patch.object(provider, "_start_quilc") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(start_quilc=True, start_qvm=False)

        mock_start.assert_called_once_with(fake_binary)

    def test_setup_calls_download_forest_sdk_when_binary_missing(
        self, mock_qcs_client: MagicMock
    ) -> None:
        """When quilc binary is not found, download_forest_sdk should be called."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch(f"{_PROVIDER_MODULE}.is_port_in_use", return_value=False),
            patch(f"{_PROVIDER_MODULE}.find_binary", return_value=None),
            patch(
                f"{_PROVIDER_MODULE}.download_forest_sdk",
                side_effect=RigettiProviderError("not found"),
            ) as mock_download,
            patch.object(provider, "_register_cleanup"),
        ):
            with pytest.raises(RigettiProviderError):
                provider.setup(start_quilc=True, start_qvm=False)

        mock_download.assert_called_once()

    def test_setup_skips_qvm_when_endpoint_provided(self, mock_qcs_client: MagicMock) -> None:
        """When qvm_endpoint is given, no local qvm process should be started."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with (
            patch.object(provider, "_start_qvm") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(
                qvm_endpoint="http://remote:5000",
                start_quilc=False,
                start_qvm=True,
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
            patch(f"{_PROVIDER_MODULE}.is_port_in_use", return_value=False),
            patch(f"{_PROVIDER_MODULE}.find_binary", return_value=fake_binary),
            patch.object(provider, "_start_qvm") as mock_start,
            patch.object(provider, "_register_cleanup"),
        ):
            provider.setup(start_quilc=False, start_qvm=True)

        mock_start.assert_called_once_with(fake_binary)

    def test_setup_registers_cleanup(self, mock_qcs_client: MagicMock) -> None:
        """setup() should always call _register_cleanup at the end."""
        provider = RigettiProvider(qcs_client=mock_qcs_client)

        with patch.object(provider, "_register_cleanup") as mock_register:
            provider.setup(start_quilc=False, start_qvm=False)

        mock_register.assert_called_once()

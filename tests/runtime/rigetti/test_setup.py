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

"""Unit tests for qbraid.runtime.rigetti.setup utilities."""

from __future__ import annotations

import importlib.util
from unittest.mock import MagicMock, patch

import pytest

from .conftest import DUMMY_CLIENT_ID, DUMMY_ISSUER, DUMMY_TOKEN

pyquil_found = importlib.util.find_spec("pyquil") is not None
pytestmark = pytest.mark.skipif(not pyquil_found, reason="pyquil not installed")

if pyquil_found:
    from qbraid.runtime.rigetti.setup import (
        RigettiProviderError,
        build_qcs_client,
        download_forest_sdk,
        find_binary,
        is_port_in_use,
        wait_for_port,
    )

_SETUP_MODULE = "qbraid.runtime.rigetti.setup"


class TestBuildQcsClient:
    """Tests for the standalone function build_qcs_client."""

    def test_build_qcs_client_uses_default_auth_server_when_no_client_id(self) -> None:
        """When client_id is None, AuthServer.default() should be used."""
        with (
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession") as mock_oauth_cls,
            patch(f"{_SETUP_MODULE}.RefreshToken") as mock_rt_cls,
            patch(f"{_SETUP_MODULE}.QCSClient") as mock_qcs_cls,
        ):
            fake_auth = MagicMock(name="DefaultAuthServer")
            mock_auth_cls.default.return_value = fake_auth
            mock_rt_cls.return_value = MagicMock(name="RefreshToken")
            mock_oauth_cls.return_value = MagicMock(name="OAuthSession")
            mock_qcs_cls.return_value = MagicMock(name="QCSClient")

            build_qcs_client(refresh_token=DUMMY_TOKEN)

            mock_auth_cls.default.assert_called_once()
            mock_auth_cls.assert_not_called()

    def test_build_qcs_client_uses_default_auth_server_when_no_issuer(self) -> None:
        """When issuer is None, AuthServer.default() should be used."""
        with (
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession"),
            patch(f"{_SETUP_MODULE}.RefreshToken"),
            patch(f"{_SETUP_MODULE}.QCSClient"),
        ):
            mock_auth_cls.default.return_value = MagicMock()

            build_qcs_client(
                refresh_token=DUMMY_TOKEN,
                client_id=DUMMY_CLIENT_ID,
                issuer=None,
            )

            mock_auth_cls.default.assert_called_once()
            mock_auth_cls.assert_not_called()

    def test_build_qcs_client_uses_custom_auth_server_when_both_provided(self) -> None:
        """When both client_id and issuer are given, AuthServer(client_id, issuer) is used."""
        with (
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession"),
            patch(f"{_SETUP_MODULE}.RefreshToken"),
            patch(f"{_SETUP_MODULE}.QCSClient"),
        ):
            mock_auth_cls.return_value = MagicMock(name="CustomAuth")

            build_qcs_client(
                refresh_token=DUMMY_TOKEN,
                client_id=DUMMY_CLIENT_ID,
                issuer=DUMMY_ISSUER,
            )

            mock_auth_cls.assert_called_once_with(client_id=DUMMY_CLIENT_ID, issuer=DUMMY_ISSUER)
            mock_auth_cls.default.assert_not_called()

    def test_build_qcs_client_passes_url_kwargs(self) -> None:
        """URL parameters should be forwarded to QCSClient constructor."""
        with (
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession") as mock_oauth_cls,
            patch(f"{_SETUP_MODULE}.RefreshToken"),
            patch(f"{_SETUP_MODULE}.QCSClient") as mock_qcs_cls,
        ):
            mock_auth_cls.default.return_value = MagicMock()
            fake_session = MagicMock(name="OAuthSession")
            mock_oauth_cls.return_value = fake_session

            grpc = "https://custom-grpc:443"
            quilc = "tcp://custom-quilc:5555"
            qvm = "http://custom-qvm:5000"

            build_qcs_client(
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
            patch(f"{_SETUP_MODULE}.AuthServer") as mock_auth_cls,
            patch(f"{_SETUP_MODULE}.OAuthSession") as mock_oauth_cls,
            patch(f"{_SETUP_MODULE}.RefreshToken"),
            patch(f"{_SETUP_MODULE}.QCSClient") as mock_qcs_cls,
        ):
            mock_auth_cls.default.return_value = MagicMock()
            fake_session = MagicMock(name="OAuthSession")
            mock_oauth_cls.return_value = fake_session

            build_qcs_client(
                refresh_token=DUMMY_TOKEN,
                grpc_api_url=None,
                quilc_url=None,
                qvm_url=None,
            )

            mock_qcs_cls.assert_called_once_with(oauth_session=fake_session)


class TestIsPortInUse:
    """Tests for the standalone function is_port_in_use."""

    def test_returns_true_when_port_is_open(self) -> None:
        """A successful connect_ex (returns 0) means the port is in use."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with patch(f"{_SETUP_MODULE}.socket.socket", return_value=mock_sock):
            assert is_port_in_use(5555) is True

        mock_sock.connect_ex.assert_called_once_with(("127.0.0.1", 5555))

    def test_returns_false_when_port_is_closed(self) -> None:
        """A non-zero connect_ex means the port is not in use."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111  # ECONNREFUSED
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with patch(f"{_SETUP_MODULE}.socket.socket", return_value=mock_sock):
            assert is_port_in_use(5555) is False

    def test_uses_custom_host(self) -> None:
        """The host parameter should be forwarded to connect_ex."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with patch(f"{_SETUP_MODULE}.socket.socket", return_value=mock_sock):
            is_port_in_use(9999, host="10.0.0.1")

        mock_sock.connect_ex.assert_called_once_with(("10.0.0.1", 9999))


class TestFindBinary:
    """Tests for the standalone function find_binary."""

    def test_returns_path_from_shutil_which(self) -> None:
        """When shutil.which finds the binary, its path is returned."""
        with patch(f"{_SETUP_MODULE}.shutil.which", return_value="/usr/bin/quilc"):
            result = find_binary("quilc")

        from pathlib import Path

        assert result == Path("/usr/bin/quilc")

    def test_falls_back_to_qbraid_bin_dir(self) -> None:
        """When shutil.which returns None, check ~/.qbraid/rigetti/bin/."""
        from pathlib import Path

        fallback_path = Path.home() / ".qbraid" / "rigetti" / "bin" / "quilc"

        with (
            patch(f"{_SETUP_MODULE}.shutil.which", return_value=None),
            patch.object(Path, "is_file", return_value=True),
            patch(f"{_SETUP_MODULE}.os.access", return_value=True),
        ):
            result = find_binary("quilc")

        assert result == fallback_path

    def test_returns_none_when_not_found(self) -> None:
        """When neither shutil.which nor the fallback finds the binary, return None."""
        from pathlib import Path

        with (
            patch(f"{_SETUP_MODULE}.shutil.which", return_value=None),
            patch.object(Path, "is_file", return_value=False),
        ):
            result = find_binary("quilc")

        assert result is None

    def test_returns_none_when_fallback_not_executable(self) -> None:
        """When the fallback file exists but is not executable, return None."""
        from pathlib import Path

        with (
            patch(f"{_SETUP_MODULE}.shutil.which", return_value=None),
            patch.object(Path, "is_file", return_value=True),
            patch(f"{_SETUP_MODULE}.os.access", return_value=False),
        ):
            result = find_binary("quilc")

        assert result is None


class TestWaitForPort:
    """Tests for the standalone function wait_for_port."""

    def test_returns_immediately_when_port_is_open(self) -> None:
        """If the port is already accepting connections, return immediately."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with (
            patch(f"{_SETUP_MODULE}.socket.socket", return_value=mock_sock),
            patch(f"{_SETUP_MODULE}.time.monotonic", side_effect=[0.0, 0.1]),
        ):
            # Should not raise
            wait_for_port(5555, timeout=5.0)

    def test_raises_on_timeout(self) -> None:
        """If the port never opens, raise RigettiProviderError."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 111  # always refused
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        # Simulate time progressing past the deadline
        with (
            patch(f"{_SETUP_MODULE}.socket.socket", return_value=mock_sock),
            patch(
                f"{_SETUP_MODULE}.time.monotonic",
                side_effect=[0.0, 0.5, 100.0],
            ),
            patch(f"{_SETUP_MODULE}.time.sleep"),
            pytest.raises(RigettiProviderError, match="Timed out waiting for port"),
        ):
            wait_for_port(5555, timeout=5.0)

    def test_retries_until_port_opens(self) -> None:
        """Should retry polling until the port starts accepting connections."""
        mock_sock = MagicMock()
        # First two checks fail, third succeeds
        mock_sock.connect_ex.side_effect = [111, 111, 0]
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=False)

        with (
            patch(f"{_SETUP_MODULE}.socket.socket", return_value=mock_sock),
            patch(
                f"{_SETUP_MODULE}.time.monotonic",
                side_effect=[0.0, 0.5, 1.0, 1.5, 2.0],
            ),
            patch(f"{_SETUP_MODULE}.time.sleep") as mock_sleep,
        ):
            wait_for_port(5555, timeout=10.0)

        assert mock_sock.connect_ex.call_count == 3
        assert mock_sleep.call_count == 2


class TestDownloadForestSdk:
    """Tests for the standalone function download_forest_sdk."""

    def test_download_forest_sdk_raises_rigetti_provider_error(self) -> None:
        """Should raise RigettiProviderError with installation instructions."""
        with pytest.raises(RigettiProviderError, match="quilc binary not found"):
            download_forest_sdk()

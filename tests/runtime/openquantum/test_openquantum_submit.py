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

"""Unit tests for Open Quantum submission details."""
from unittest.mock import MagicMock, patch

import pytest

from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.openquantum import OpenQuantumSession


def test_device_submit_shots_mismatch(provider):
    """A shots argument that disagrees with configuration_data is rejected first."""
    device = provider.get_device("oq-sim")
    with pytest.raises(ValueError, match="shots mismatch"):
        device.submit(
            "OPENQASM 3.0; h q[0];",
            shots=100,
            configuration_data={"shots": 500},
        )
    provider.session.upload_input.assert_not_called()


def test_device_submit_rejects_bad_shots(provider):
    """Shots must be an integer, and configuration_data must be an object."""
    device = provider.get_device("oq-sim")
    with pytest.raises(ValueError, match="shots must be an integer"):
        device.submit("OPENQASM 3.0; h q[0];", shots=True)
    with pytest.raises(ValueError, match="configuration_data.shots must be an integer"):
        device.submit("OPENQASM 3.0; h q[0];", configuration_data={"shots": "100"})
    with pytest.raises(ValueError, match="configuration_data must be an object"):
        device.submit("OPENQASM 3.0; h q[0];", configuration_data=["shots"])
    provider.session.upload_input.assert_not_called()


def test_device_submit_shots_from_configuration(provider):
    """configuration_data.shots is used when the shots argument is omitted."""
    device = provider.get_device("oq-sim")
    device.submit(
        "OPENQASM 3.0; h q[0];",
        configuration_data={"engine": "SCARLET_CPU", "shots": 250},
    )
    payload = provider.session.prepare_job.call_args.args[0]
    assert payload["shots"] == 250
    assert payload["configuration_data"] == {"engine": "SCARLET_CPU", "shots": 250}
    assert "input_format" not in payload


def test_device_submit_input_format(provider):
    """input_format is sent only when the caller sets it."""
    device = provider.get_device("oq-sim")
    device.submit("OPENQASM 3.0; h q[0];", input_format="qblox_sequence", shots=10)
    payload = provider.session.prepare_job.call_args.args[0]
    assert payload["input_format"] == "qblox_sequence"
    assert payload["shots"] == 10
    assert payload["configuration_data"] == {"shots": 10}

    provider.session.prepare_job.reset_mock()
    device.submit(
        ["OPENQASM 3.0; h q[0];", "OPENQASM 3.0; x q[0];"],
        input_format="qasm",
    )
    assert provider.session.prepare_job.call_count == 2
    for call in provider.session.prepare_job.call_args_list:
        assert call.args[0]["input_format"] == "qasm"


def test_device_submit_warns_for_multiple_organizations(provider):
    """Several organizations warn and still bill the first one."""
    provider.session.get_user_organizations.return_value = [
        {"id": "org-a", "name": "Alpha"},
        {"id": "org-b", "name": "Beta"},
    ]
    device = provider.get_device("oq-sim")
    with pytest.warns(UserWarning, match="Multiple organizations found") as caught:
        device.submit("OPENQASM 3.0; h q[0];")
    message = str(caught[0].message)
    assert "Alpha (org-a)" in message
    assert "Beta (org-b)" in message
    assert provider.session.create_job.call_args.args[0]["organization_id"] == "org-a"


def test_device_submit_uses_organization_env(monkeypatch, provider):
    """OPENQUANTUM_ORGANIZATION_ID selects the organization without listing them."""
    monkeypatch.setenv("OPENQUANTUM_ORGANIZATION_ID", "  env-org  ")
    device = provider.get_device("oq-sim")
    device.submit("OPENQASM 3.0; h q[0];")
    provider.session.get_user_organizations.assert_not_called()
    assert provider.session.create_job.call_args.args[0]["organization_id"] == "env-org"


def test_device_submit_blank_organization_env_lists_orgs(monkeypatch, provider):
    """A blank organization env var falls through to the organization list."""
    monkeypatch.setenv("OPENQUANTUM_ORGANIZATION_ID", "   ")
    device = provider.get_device("oq-sim")
    device.submit("OPENQASM 3.0; h q[0];")
    provider.session.get_user_organizations.assert_called_once()
    assert provider.session.create_job.call_args.args[0]["organization_id"] == "org_abc123"


def test_device_submit_organization_missing_id(provider):
    """An organization row without an id is an error."""
    provider.session.get_user_organizations.return_value = [{"name": "Nameless"}]
    device = provider.get_device("oq-sim")
    with pytest.raises(QbraidRuntimeError, match="Organization is missing an id."):
        device.submit("OPENQASM 3.0; h q[0];")


def test_session_get_user_organizations_pagination():
    """Organization listing follows next_cursor and requests full pages."""
    session = OpenQuantumSession(client_id="id", client_secret="secret")
    with patch.object(session, "get") as mock_get:
        first = MagicMock()
        first.json.return_value = {
            "organizations": [{"id": "org-1"}],
            "pagination": {"next_cursor": "cursor_1"},
        }
        second = MagicMock()
        second.json.return_value = {
            "organizations": [{"id": "org-2"}],
            "pagination": {"next_cursor": None},
        }
        mock_get.side_effect = [first, second]

        orgs = session.get_user_organizations()
        assert [org["id"] for org in orgs] == ["org-1", "org-2"]
        assert mock_get.call_args_list[0].kwargs["params"] == {"limit": 100}
        assert mock_get.call_args_list[1].kwargs["params"] == {"limit": 100, "cursor": "cursor_1"}

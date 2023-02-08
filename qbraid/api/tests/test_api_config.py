# Copyright 2023 qBraid
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
Unit tests related to setting, updating, and verifying
custom user configurations and required run-command pre-sets.

"""
import configparser
import os

import pytest

from qbraid.api.config_data import (
    aws_config_path,
    aws_cred_path,
    ibmq_account_url,
    qbraid_api_url,
    qbraid_config_path,
    qbraidrc_path,
    qiskitrc_path,
)
from qbraid.api.config_prompt import _mask_value
from qbraid.api.config_user import get_config, update_config, verify_config
from qbraid.api.exceptions import ConfigError, RequestsApiError
from qbraid.api.ibmq_api import ibmq_get_provider
from qbraid.api.session import QbraidSession

# These environment variables don't actually exist in qBraid Lab, but instead
# are set and used for convenience for local development and testing.
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
ibmq_token = os.getenv("IBMQ_TOKEN")
qbraid_token = os.getenv("REFRESH")

# This is the only environment variable that actually exists in qBraid Lab
qbraid_user = os.getenv("JUPYTERHUB_USER")

config_lst = [
    # (config_name, config_value, section, filepath)
    ["aws_access_key_id", aws_access_key_id, "default", aws_cred_path],
    ["aws_secret_access_key", aws_secret_access_key, "default", aws_cred_path],
    ["region", "us-east-1", "default", aws_config_path],
    ["output", "json", "default", aws_config_path],
    ["s3_bucket", "amazon-braket-qbraid-test", "AWS", qbraid_config_path],
    ["s3_folder", "qbraid-sdk-output", "AWS", qbraid_config_path],
    ["verify", "True", "AWS", qbraid_config_path],
    ["token", ibmq_token, "ibmq", qiskitrc_path],
    ["url", ibmq_account_url, "ibmq", qiskitrc_path],
    ["verify", "True", "ibmq", qiskitrc_path],
    ["default_provider", "ibm-q/open/main", "ibmq", qiskitrc_path],
    # In qBraid Lab, the qbraidrc file is automatically generated through the API
    ["email", qbraid_user, "default", qbraidrc_path],
    ["url", qbraid_api_url, "default", qbraidrc_path],
    ["refresh-token", qbraid_token, "default", qbraidrc_path],
]


def set_config():
    """Set config inside testing virtual environments with default values
    hard-coded and secret values read from environment variables.

    Note: this function is used in lieu of :func:`~qbraid.api.config_user._set_config`
    to by-pass the user prompt, and directly set the configs to be used to testing."""
    for file in [aws_config_path,aws_cred_path, qbraid_config_path, qbraidrc_path, qiskitrc_path]:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
    for c in config_lst:
        config_name = c[0]
        config_value = c[1]
        section = c[2]
        filepath = c[3]
        if not os.path.isfile(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        config = configparser.ConfigParser()
        config.read(filepath)
        if section not in config.sections():
            config.add_section(section)
        config.set(section, config_name, str(config_value))
        with open(filepath, "w", encoding="utf-8") as cfgfile:
            config.write(cfgfile)


def test_verify_config():
    """Test raising error when verifying invalid qbraid config."""
    # remove qbraidrc file if it already exists
    try:
        os.remove(qbraidrc_path)
    except FileNotFoundError:
        pass
    with pytest.raises(ConfigError):
        verify_config("QBRAID")


def test_update_config():
    """Test updating user config."""
    # test returning -1 when config doesn't exists
    assert get_config("refresh-token", "default") == -1
    # updating config with no input sets them to None
    update_config("QBRAID", exists=False)
    assert get_config("refresh-token", "default") == "None"
    # set correct config
    set_config()
    assert get_config("refresh-token", "default") == os.getenv("REFRESH")


@pytest.mark.parametrize("testdata", [("abc123", "******abc123"), (None, "None")])
def test_mask_value(testdata):
    """Test applying mask to user prompt value."""
    value, expected = testdata
    mask = _mask_value(value)
    assert mask == expected


def test_api_error():
    """Test raising error when making invalid API request."""
    with pytest.raises(RequestsApiError):
        session = QbraidSession()
        session.request("POST", "not a url")


@pytest.mark.parametrize("config", config_lst)
def test_get_config(config):
    """Test getting config value."""
    set_config()
    name = config[0]
    value = config[1]
    section = config[2]
    path = config[3]
    get_value = get_config(name, section, filepath=path)
    assert value == get_value


def test_qbraid_session_from_args():
    """Test initializing QbraidSession with attributes set from user-provided values."""
    id_token = "test123"
    session = QbraidSession(id_token=id_token)
    assert session.id_token == id_token


def test_qbraid_session_from_config():
    """Test initializing QbraidSession with attributes auto-set from config values."""
    user_email = get_config("email", "default")
    session = QbraidSession()
    assert session.user_email == user_email
    res = session.get("/identity")
    assert user_email == res.json()["email"]


def test_ibmq_get_provider():
    """Test getting IBMQ provider from qiskitrc"""
    from qiskit.providers.ibmq import AccountProvider

    set_config()
    provider = ibmq_get_provider()
    assert isinstance(provider, AccountProvider)

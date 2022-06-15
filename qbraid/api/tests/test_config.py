"""
Unit tests related to setting, updating, and verifying
custom user configurations and required run-command pre-sets.

"""
import configparser
import os

import pytest

from qbraid.api.config_specs import (
    aws_config_path,
    aws_cred_path,
    ibmq_account_url,
    qbraid_api_url,
    qbraid_config_path,
    qbraidrc_path,
    qiskitrc_path,
)
from qbraid.api.config_user import _mask_value, get_config, update_config, verify_config
from qbraid.api.exceptions import ConfigError, RequestsApiError
from qbraid.api.session import QbraidSession
from qbraid.api.ibmq_api import ibmq_get_provider

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
    for c in config_lst:
        config_name = c[0]
        config_value = c[1]
        section = c[2]
        filepath = c[3]
        # print(f"{config_name}: {config_value}")
        if not os.path.isfile(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        config = configparser.ConfigParser()
        config.read(filepath)
        if section not in config.sections():
            config.add_section(section)
        config.set(section, config_name, str(config_value))
        with open(filepath, "w", encoding="utf-8") as cfgfile:
            config.write(cfgfile)


def test_update_config():
    """Test updating user config."""
    # remove qbraidrc file if it already exists
    try:
        os.remove(qbraidrc_path)
    except FileNotFoundError:
        pass
    # test returning -1 when config doesn't exists
    assert get_config("refresh-token", "default") == -1
    # updating config with no input sets them to None
    update_config("QBRAID", exists=False)
    assert get_config("refresh-token", "default") == "None"
    # remove qbraidrc file again and set correct config
    os.remove(qbraidrc_path)
    set_config()
    assert get_config("refresh-token", "default") == os.getenv("REFRESH")


@pytest.mark.parametrize("testdata", [("abc123", "******abc123"), (None, "None")])
def test_mask_value(testdata):
    """Test applying mask to user prompt value."""
    value, expected = testdata
    mask = _mask_value(value)
    assert mask == expected


def test_verify_config():
    """Test raising error when verifying invalid qbraid config."""
    with pytest.raises(ConfigError):
        verify_config("QBRAID")


def test_api_error():
    """Test raising error when making invalid API request."""
    with pytest.raises(RequestsApiError):
        session = QbraidSession()
        session.request("POST", "not a url")


set_config()  # TODO: double-check that this isn't redundant with ``test_update_cofig``


@pytest.mark.parametrize("config", config_lst)
def test_get_config(config):
    """Test getting config value."""
    name = config[0]
    value = config[1]
    section = config[2]
    path = config[3]
    get_value = get_config(name, section, filepath=path)
    assert value == get_value


def test_qbraid_session_from_config():
    """Test initializing QbraidSession with attributes auto-set from config values."""
    email = get_config("email", "default")
    refresh = get_config("refresh-token", "default")
    session = QbraidSession()
    headers = session.headers
    assert headers["email"] == email
    assert headers["refresh-token"] == refresh


def test_qbraid_session_from_args():
    """Test initializing QbraidSession with attributes set from user-provided values."""
    email = "test"
    refresh = "123"
    session = QbraidSession(user_email=email, refresh_token=refresh)
    headers = session.headers
    assert headers["email"] == email
    assert headers["refresh-token"] == refresh


def test_ibmq_get_provider():
    """Test getting IBMQ provider from qiskitrc"""
    from qiskit.providers.ibmq import AccountProvider

    provider = ibmq_get_provider()
    assert isinstance(provider, AccountProvider)

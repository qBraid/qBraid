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

from qbraid.api.exceptions import RequestsApiError
from qbraid.api.session import QbraidSession

aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws", "credentials")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws", "config")
qiskitrc_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")
qbraidrc_path = os.path.join(os.path.expanduser("~"), ".qbraid", "qbraidrc")

# These environment variables don't actually exist in qBraid Lab, but instead
# are set and used for convenience for local development and testing.
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
ibmq_token = os.getenv("QISKIT_IBM_TOKEN")
qbraid_token = os.getenv("REFRESH")

# This is the only environment variable that actually exists in qBraid Lab
qbraid_user = os.getenv("JUPYTERHUB_USER")

config_lst = [
    # (config_name, config_value, section, filepath)
    ["aws_access_key_id", aws_access_key_id, "default", aws_cred_path],
    ["aws_secret_access_key", aws_secret_access_key, "default", aws_cred_path],
    ["region", "us-east-1", "default", aws_config_path],
    ["output", "json", "default", aws_config_path],
    ["token", ibmq_token, "ibmq", qiskitrc_path],
    ["url", "https://auth.quantum-computing.ibm.com/api", "ibmq", qiskitrc_path],
    ["verify", "True", "ibmq", qiskitrc_path],
    ["default_provider", "ibm-q/open/main", "ibmq", qiskitrc_path],
]


def set_config():
    """Set config inside testing virtual environments with default values
    hard-coded and secret values read from environment variables.

    Note: this function is used for testing purposes only."""
    for file in [aws_config_path, aws_cred_path, qiskitrc_path]:
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


def test_api_error():
    """Test raising error when making invalid API request."""
    with pytest.raises(RequestsApiError):
        session = QbraidSession()
        session.request("POST", "not a url")


def test_qbraid_session_from_args():
    """Test initializing QbraidSession with attributes set from user-provided values."""
    refresh_token = "test123"
    session = QbraidSession(refresh_token=refresh_token)
    assert session.refresh_token == refresh_token
    del session


def test_qbraid_session_from_config():
    """Test initializing QbraidSession with attributes auto-set from config values."""
    try:
        QbraidSession()
    except Exception:
        assert False
    assert True

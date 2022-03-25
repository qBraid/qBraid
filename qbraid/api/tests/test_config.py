import os

import pytest

from qbraid.api.config_specs import (
    aws_config_path,
    aws_cred_path,
    qiskitrc_path,
    ibmq_account_url,
    qbraid_api_url,
    qbraid_config_path,
    qbraidrc_path,
)
from qbraid.api.config_user import get_config
from qbraid.api.session import QbraidSession

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
ibmq_token = os.getenv("IBMQ_TOKEN")
qbraid_user = os.getenv("JUPYTERHUB_USER")
qbraid_token = os.getenv("REFRESH")

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
    ["group", "open", "IBM", qbraid_config_path],
    ["project", "main", "IBM", qbraid_config_path],
    ["verify", "True", "IBM", qbraid_config_path],
    ["email", qbraid_user, "default", qbraidrc_path],
    ["refresh-token", qbraid_token, "default", qbraidrc_path],
    ["url", qbraid_api_url, "default", qbraidrc_path],
]


@pytest.mark.parametrize("config", config_lst)
def test_get_config(config):
    name = config[0]
    value = config[1]
    section = config[2]
    path = config[3]
    get_value = get_config(name, section, filepath=path)
    assert value == get_value


def test_qbraid_session_from_config():
    email = get_config("email", "default", filepath=qbraidrc_path)
    refresh = get_config("refresh-token", "default", filepath=qbraidrc_path)
    session = QbraidSession()
    headers = session.headers
    assert headers["email"] == email
    assert headers["refresh-token"] == refresh


def test_qbraid_session_from_args():
    email = "test"
    refresh = "123"
    session = QbraidSession(user_email=email, auth_token=refresh)
    headers = session.headers
    assert headers["email"] == email
    assert headers["refresh-token"] == refresh

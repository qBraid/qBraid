import pytest

from qbraid.api.config_user import get_config
from qbraid.api.session import QbraidSession
from qbraid.api.tests.config_venv import config_lst, qbraidrc_path


@pytest.mark.parametrize("config", config_lst)
def test_get_config(config):
    name = config[0]
    value = config[1]
    section = config[2]
    path = config[3]
    get_value = get_config(name, section, filepath=path)
    assert value == get_value


def test_qbraid_session_from_config():
    email = get_config("user", "sdk", filepath=qbraidrc_path)
    refresh = get_config("token", "sdk", filepath=qbraidrc_path)
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

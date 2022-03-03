import pytest

from qbraid.api.config_user import get_config
from qbraid.api.tests.config_venv import config_lst


@pytest.mark.parametrize("config", config_lst)
def test_get_config(config):
    name = config[0]
    value = config[1]
    section = config[2]
    path = config[3]
    get_value = get_config(name, section, filepath=path)
    assert value == get_value

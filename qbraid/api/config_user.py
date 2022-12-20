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
Module for creating and modifying user config files.

"""
import configparser
import os
from typing import Optional, Union

from .config_data import CONFIG_PATHS, VENDOR_CONFIGS
from .config_prompt import _set_config
from .exceptions import ConfigError


def verify_config(vendor: str) -> int:
    """Checks for the required user credentials associated with running on device
    associated with given vendor. If requirements are verified, returns ``0``. Else,
    calls :func:`~qbraid.api.set_config`, and returns 0 after credentials are provided
    and config is successfully made.

    Args:
        vendor: A supported vendor

    Returns:
        Exit code ``0`` if config is valid.

    Raises:
        :class:`~qbraid.api.ConfigError`: If config is not valid.

    """
    prompt_lst = VENDOR_CONFIGS[vendor]
    if vendor == "QBRAID":
        url = get_config("url", "default")
        email = get_config("email", "default")
        refresh_token = get_config("refresh-token", "default")
        id_token = get_config("id-token", "default")
        try:
            if url + email + max(refresh_token, id_token) == -3:
                raise ConfigError("Invalid qbraidrc")
        except TypeError as err:
            raise ConfigError("Invalid qbraidrc") from err
    else:
        file_dict = CONFIG_PATHS[vendor]
        for file in file_dict:
            filepath = file_dict[file]
            for prompt in prompt_lst:
                name = prompt[0]
                section = prompt[4]
                value = get_config(name, section, filepath=filepath)
                if value == -1:
                    _set_config(*prompt)
                elif value in ["", "None"]:
                    _set_config(*prompt, update=True)
    return 0


def get_config(config_name: str, section: str, filepath: Optional[str] = None) -> Union[str, int]:
    """Returns the config value of specified config. If vendor and filename
    are not specified, filepath must be specified.

    Args:
        config_name: The name of the config
        section: The section of the config file to store config_name
        filepath: The existing or desired path to config file.

    Returns:
        Config value or ``-1`` if config does not exist

    """
    if not filepath:
        filename = "qbraidrc" if section == "default" else "config"
        filepath = CONFIG_PATHS["QBRAID"][filename]
    if os.path.isfile(filepath):
        config = configparser.ConfigParser()
        config.read(filepath)
        if section in config.sections():
            if config_name in config[section]:
                return config[section][config_name]
    return -1


def update_config(vendor: str, exists=True) -> int:
    """Update the config associated with given vendor

    Args:
        vendor (str): A supported vendor

    Returns:
        Exit code ``0`` if update is successful.

    Raises:
        :class:`~qbraid.api.ConfigError`: If there is an error updating the config.

    """
    prompt_lst = VENDOR_CONFIGS[vendor]
    for prompt in prompt_lst:
        _set_config(*prompt, update=exists)
    return 0

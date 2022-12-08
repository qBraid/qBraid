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
Module for prompting user and setting config values.

"""
import configparser
import os
import sys
from getpass import getpass
from typing import Optional

from .exceptions import ConfigError

raw_input = input
secret_input = getpass


def _mask_value(value: Optional[str]) -> str:
    """Replaces all but last four characters of token ``value`` with *'s"""
    if value is None:
        return "None"
    val = round(len(value) / 5)
    len_hint = 4 if val > 4 else 0 if val < 2 else val
    default_stars = len(value) - len_hint
    len_stars = default_stars if default_stars <= 16 else 16
    return ("*" * len_stars) + value[-len_hint:]


def _get_value(display_value: str, is_secret: bool, prompt_text: str) -> str:
    """Applies mask to ``display_value`` and prompts user"""
    display_value = _mask_value(display_value) if is_secret else display_value
    response = _compat_input(f"{prompt_text} [{display_value}]: ", is_secret)
    if not response:
        response = None
    return response


def _compat_input(prompt: str, is_secret: bool) -> str:
    """Prompts user for value"""
    if is_secret:
        return secret_input(prompt=prompt)
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return raw_input()


def _set_config(  # pylint: disable=too-many-arguments
    config_name: str,
    prompt_text: str,
    default_val: Optional[str],
    is_secret: bool,
    section: str,
    filepath: str,
    update: Optional[bool] = False,
) -> int:
    """Adds or modifies a user configuration

    Args:
        config_name: The name of the config
        prompt_text: The text that will prompt the user to enter config_name.
        default_val: The default value for config name
        is_secret: Specifies if the value of this config should be kept private
        section: The section of the config file to store config_name
        filepath: The existing or desired path to config file
        update: True if user is updating an already existing config

    Returns:
        Exit code 0 if config set was successful.

    Raises:
        :class:`~qbraid.api.ConfigError`: If unable to load file from specified ``filename``.

    """
    if not os.path.isfile(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    config = configparser.ConfigParser()
    config.read(filepath)
    current_val = None
    if section not in config.sections():
        config.add_section(section)
    else:
        if config_name in config[section]:
            current_val = config[section][config_name]
            if current_val not in ["", "None", None] and update is False:
                return 0
    if len(prompt_text) == 0:
        config_val = default_val
    else:
        display_val = current_val if current_val not in ["", "None", None] else default_val
        new_val = _get_value(display_val, is_secret, prompt_text)
        config_val = new_val if new_val not in ["", "None", None] else display_val
    config.set(section, config_name, str(config_val))
    try:
        with open(filepath, "w", encoding="utf-8") as cfgfile:
            config.write(cfgfile)
    except OSError as err:
        raise ConfigError(f"Unable to load the config file {filepath}. ") from err
    return 0

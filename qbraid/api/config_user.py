"""Module for creating and modifying user config files"""

import configparser
import os
import sys
from getpass import getpass
from typing import Optional, Union

from .config_specs import CONFIG_PATHS, VENDOR_CONFIGS
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

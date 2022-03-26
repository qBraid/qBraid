"""Module for creating and modifying user config files"""

# pylint: disable=too-many-arguments

import configparser
import os
import sys
from getpass import getpass

from .config_specs import CONFIG_PATHS, VENDOR_CONFIGS
from .exceptions import ConfigError

raw_input = input
secret_input = getpass


def mask_value(value):
    """Replaces all but last four characters of token ``value`` with *'s"""
    if value is None:
        return "None"
    val = round(len(value) / 5)
    len_hint = 4 if val > 4 else 0 if val < 2 else val
    default_stars = len(value) - len_hint
    len_stars = default_stars if default_stars <= 16 else 16
    return ("*" * len_stars) + value[-len_hint:]


def get_value(display_value, is_secret, prompt_text):
    """Applies mask to ``display_value`` and prompts user"""
    display_value = mask_value(display_value) if is_secret else display_value
    response = compat_input(f"{prompt_text} [{display_value}]: ", is_secret)
    if not response:
        response = None
    return response


def compat_input(prompt, is_secret):
    """Prompts user for value"""
    if is_secret:
        return secret_input(prompt=prompt)
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return raw_input()


def set_config(config_name, prompt_text, default_val, is_secret, section, filepath, update=False):
    """Adds or modifies a user configuration

    Args:
        config_name (str): the name of the config
        prompt_text (str): the text that will prompt the user to enter config_name.
        default_val (None, str): default value for config name
        is_secret (bool) = specifies if the value of this config should be kept private
        section (str) = the section of the config file to store config_name
        filepath (str): the existing or desired path to config file
        update (optional, bool): True if user is updating an already existing config

    Raises:
        ConfigError if unable to load file from specified ``filename``.

    """
    if not os.path.isfile(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    config = configparser.ConfigParser()
    config.read(filepath)
    current_value = None
    if section in config.sections():
        if config_name in config[section]:
            current_value = config[section][config_name]
            if current_value is not None and update is False:
                return 0
    else:
        config.add_section(section)
    if len(prompt_text) == 0:
        new_value = default_val
    else:
        display_value = default_val if current_value is None else current_value
        new_value = get_value(display_value, is_secret, prompt_text)
    config_val = default_val if new_value is None else new_value
    config.set(section, config_name, str(config_val))
    try:
        with open(filepath, "w", encoding="utf-8") as cfgfile:
            config.write(cfgfile)
    except OSError as err:
        raise ConfigError(f"Unable to load the config file {filepath}. ") from err
    return 0


def verify_config(vendor):
    """Checks for the required user credentials associated with running on device associated with
    given vendor. If requirements are verified, returns 0. Else, calls set_config, and returns 0
    after credentials are provided and config is successfully made.

    """
    prompt_lst = VENDOR_CONFIGS[vendor]
    if vendor == "QBRAID":
        url = get_config("url", "default")
        email = get_config("email", "default")
        refresh_token = get_config("refresh-token", "default")
        id_token = get_config("id-token", "default")
        if url + email + max(refresh_token, id_token) == -3:
            raise ConfigError("Invalid qbraidrc")
    else:
        file_dict = CONFIG_PATHS[vendor]
        for file in file_dict:
            filepath = file_dict[file]
            if get_config("verify", vendor, filepath=filepath) != "True":
                for prompt in prompt_lst:
                    set_config(*prompt)
    return 0


def get_config(config_name, section, filepath=None):
    """Returns the config value of specified config. If vendor and filename
    are not specified, filepath must be specified.

    Args:
        config_name (str): the name of the config
        section (str) = the section of the config file to store config_name
        filepath (optional, str): the existing or desired path to config file.
    Returns:
        Config value or -1 if config does not exist
    """
    if not filepath:
        filename = "qbraidrc" if section == "default" else "config"
        try:
            filepath = CONFIG_PATHS["QBRAID"][filename]
        except KeyError:
            return -1
    if os.path.isfile(filepath):
        config = configparser.ConfigParser()
        config.read(filepath)
        if section in config.sections():
            if config_name in config[section]:
                return config[section][config_name]
    return -1


def update_config(vendor, update=True):
    """Update the config associated with given vendor

    Args:
        vendor (str): a supported vendor

    """
    prompt_lst = VENDOR_CONFIGS[vendor]
    for prompt in prompt_lst:
        set_config(*prompt, update=update)
    return 0

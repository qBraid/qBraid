import configparser
from getpass import getpass
import os
import sys

from qbraid.devices.exceptions import ConfigError

raw_input = input
secret_input = getpass


def mask_value(current_value):
    if current_value is None:
        return "None"
    val = round(len(current_value) / 5)
    len_hint = 4 if val > 4 else 0 if val < 2 else val
    default_stars = len(current_value) - len_hint
    len_stars = default_stars if default_stars <= 16 else 16
    return ("*" * len_stars) + current_value[-len_hint:]


def get_value(current_value, is_secret, prompt_text):
    display_value = mask_value(current_value) if is_secret else current_value
    response = compat_input("%s [%s]: " % (prompt_text, display_value), is_secret)
    if not response:
        response = None
    return response


def compat_input(prompt, is_secret):
    if is_secret:
        return secret_input(prompt=prompt)
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return raw_input()


def set_config(config_name, prompt_text, default_value, is_secret, section, filepath, update=False):
    """Adds or modifies a user configuration

    Args:
        config_name (str): the name of the config
        prompt_text (str): the text that will prompt the user to enter config_name.
        default_value (None, str): default value for config name
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
            if not (current_value is None or update):
                return 0
    else:
        config.add_section(section)
    if len(prompt_text) == 0:
        new_value = default_value
    else:
        new_value = get_value(current_value, is_secret, prompt_text)
    config_val = default_value if new_value is None else new_value
    config.set(section, config_name, str(config_val))
    try:
        with open(filepath, "w") as cfgfile:
            config.write(cfgfile)
    except OSError as ex:
        raise ConfigError(f"Unable to load the config file {filepath}. Error: '{str(ex)}'")
    return 0


def get_config(config_name, section, filepath):
    """Returns the config value of specified config

    Args:
        config_name (str): the name of the config
        section (str) = the section of the config file to store config_name
        filepath (str): the existing or desired path to config file

    Raises:
        ConfigError if config_name, section or filepath do not exist.

    """
    if not os.path.isfile(filepath):
        raise ConfigError(f"Config file {filepath} does not exist.")
    config = configparser.ConfigParser()
    config.read(filepath)
    if section not in config.sections():
        raise ConfigError(f"Config section {section} does not exist.")
    if config_name not in config[section]:
        raise ConfigError(f"Config {config_name} does not exist.")
    config_value = config[section][config_name]
    return config_value

import configparser
from getpass import getpass
import os
import sys

from qbraid.devices.exceptions import ConfigError

raw_input = input
secret_input = getpass


def mask_value(current_value):
    if current_value is None:
        return 'None'
    val = round(len(current_value) / 5)
    len_hint = 4 if val > 4 else 0 if val < 2 else val
    return ('*' * (len(current_value) - len_hint)) + current_value[-len_hint:]


def get_value(current_value, is_secret, prompt_text=''):
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


def set_config(config_name, prompt_text, is_secret, section, filepath):
    """Adds or modifies a user configuration

    Args:
        config_name (str): the name of the config
        prompt_text (str): the text that will prompt the user to enter config_name
        is_secret (bool) = specifies if the value of this config should be kept private
        section (str) = the section of the config file to store config_name
        filepath (str): the existing or desired path to config file

    Raises:
        Exception if unable to load file from specified ``filename``.

    """
    if not os.path.isfile(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    config = configparser.ConfigParser()
    config.read(filepath)
    current_value = None
    if section in config.sections():
        if config_name in config[section]:
            current_value = config[section][config_name]
    else:
        config.add_section(section)
    new_value = get_value(current_value, is_secret, prompt_text)
    if new_value is not None and new_value != current_value:
        config.set(section, config_name, str(new_value))
    try:
        with open(filepath, "w") as cfgfile:
            config.write(cfgfile)
    except OSError as ex:
        raise ConfigError(f"Unable to load the config file {filepath}. Error: '{str(ex)}'")
    return 0


def validate_config(vendor):
    # TO DO: validate configuration for given vendor
    return False

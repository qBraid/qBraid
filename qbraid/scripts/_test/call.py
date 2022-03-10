"""Module for pythonic calls to qbraid bash scripts"""

import configparser
import enum
import errno
import os
import platform
import subprocess


class Runner(enum.Enum):
    """Class for the types runtime environments."""

    MACOS = "Darwin"
    UBUNTU = "Linux"


def get_runner():
    system = platform.system()
    return Runner(system)


RUNNER = get_runner()

dir_path = os.path.dirname(os.path.realpath(__file__))

qbraidrc_path = os.path.join(os.path.expanduser("~"), ".qbraid", "qbraidrc")
qbraid_config_path = os.path.join(os.path.expanduser("~"), ".qbraid", "config")
aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws", "credentials")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws", "config")

# qbraid_api_url = "http://localhost:3001/api"
# qbraid_api_url = "https://api-staging.qbraid.com/api"
# qbraid_api_url_URL = "https://api.qbraid.com/api"
qbraid_api_url = "https://api-staging-1.qbraid.com/api"

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
    ["user", qbraid_user, "sdk", qbraidrc_path],
    ["token", qbraid_token, "sdk", qbraidrc_path],
    ["url", qbraid_api_url, "QBRAID", qbraid_config_path],
    ["verify", "True", "QBRAID", qbraid_config_path],
]


def set_config():
    """Set config inside testing virtual environments with default values
    hard-coded and secret values read from environment variables."""
    for c in config_lst:
        config_name = c[0]
        config_value = c[1]
        section = c[2]
        filepath = c[3]
        # print(f"{config_name}: {config_value}")
        if not os.path.isfile(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
        config = configparser.ConfigParser()
        config.read(filepath)
        if section not in config.sections():
            config.add_section(section)
        config.set(section, config_name, str(config_value))
        with open(filepath, "w", encoding="utf-8") as cfgfile:
            config.write(cfgfile)


def _get_scripts():
    return list(filter(lambda x: x[-3:] == ".sh", os.listdir(dir_path)))


def _call_script(script):
    script_path = os.path.join(dir_path, script)
    if not os.path.exists(script_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), script)
    subprocess.call([script_path])


def delete_configs():
    _call_script("delete-configs.sh")


def initialize_session():
    """Populate headers to enable QbraidSession"""
    _call_script("update-headers.sh")


def close_session():
    """Strip headers to close QbraidSession"""
    _call_script("strip-headers.sh")

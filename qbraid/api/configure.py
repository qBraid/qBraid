"""
Module containing function to set qBraid credentials

"""
import configparser
import os

from qbraid.api.exceptions import AuthError, ConfigError
from qbraid.api.session import QbraidSession


def configure(user_email=None, api_token=None):
    """Create qbraidrc file. In qBraid Lab, qbraidrc file is automatically
    present in filesystem."""
    if user_email is None:
        jupyter_user = os.getenv("JUPYTERHUB_USER")
        if jupyter_user is None:
            raise AuthError(f"Invalid qBraid user email, {user_email}")
        user_email = jupyter_user

    if api_token is None:
        raise AuthError(f"Invalid qBraid API token, {api_token}")

    qbraid_api_url = "https://api-staging-1.qbraid.com/api"

    session = QbraidSession(user_email=user_email, refresh_token=api_token)
    session.base_url = qbraid_api_url

    res = session.get("/identity")

    if res.status_code != 200 or user_email != res.json()["email"]:
        raise AuthError("Invalid qBraid API credentials")

    try:
        section = "default"
        qbraidrc_path = os.path.join(os.path.expanduser("~"), ".qbraid", "qbraidrc")
        if not os.path.isfile(qbraidrc_path):
            os.makedirs(os.path.dirname(qbraidrc_path), exist_ok=True)
        config = configparser.ConfigParser()
        config.read(qbraidrc_path)
        if section not in config.sections():
            config.add_section(section)
        config.set(section, "email", user_email)
        config.set(section, "url", qbraid_api_url)
        config.set(section, "refresh-token", api_token)
        with open(qbraidrc_path, "w", encoding="utf-8") as cfgfile:
            config.write(cfgfile)
    except Exception as err:
        raise ConfigError from err

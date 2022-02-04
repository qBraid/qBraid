"""Module to pip install"""

import logging
import subprocess
import sys

import qbraid


def install(package: str):
    """Executes ``python -m pip install package`` for given ``package``"""
    logging.info("Installing %s....", package)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as err:
        raise qbraid.QbraidError(f"Failed to install {package}") from err

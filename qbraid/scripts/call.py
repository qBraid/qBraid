"""Module for pythonic calls to qbraid bash scripts"""

import errno
import os
import subprocess

dir_path = os.path.dirname(os.path.realpath(__file__))


def _get_scripts():
    return list(filter(lambda x: x[-3:] == ".sh", os.listdir(dir_path)))


def _call_script(script):
    script_path = os.path.join(dir_path, script)
    if not os.path.exists(script_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), script)
    subprocess.call([script_path])


def initialize_session():
    """Populate headers to enable QbraidSession"""
    _call_script("update-headers.sh")


def close_session():
    """Strip headers to close QbraidSession"""
    _call_script("strip-headers.sh")

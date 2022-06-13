"""
Unit tests for functions that utilize, interact with,
or relate to qBraid Quantum Jobs.

"""
import os

from qbraid.api.job_api import _braket_proxy


def test_check_braket_proxy():
    """Test function that checks whether braket proxy is active."""
    home = os.getenv("HOME")
    lab_envs = f"{home}/.qbraid/environments"
    lab_slug = "qbraid_sdk_9j9sjy"
    package = "botocore"
    proxy_dir = f"{lab_envs}/{lab_slug}/qbraid/{package}"
    proxy_file = f"{proxy_dir}/proxy"
    os.makedirs(proxy_dir, exist_ok=True)
    if os.path.exists(proxy_file):
        os.remove(proxy_file)
    assert _braket_proxy() is False
    outF = open(proxy_file, "w")
    outF.writelines("active = true\n")
    outF.close()
    assert _braket_proxy() is True
    os.remove(proxy_file)

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
Unit tests for functions that utilize, interact with,
or relate to qBraid other third-party APIs.

"""
import os

import pytest

from qbraid.api.ibmq_api import ibmq_least_busy_qpu
from qbraid.api.job_api import _braket_proxy
from qbraid.api.session import STATUS_FORCELIST, PostForcelistRetry, QbraidSession


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


def test_ibmq_least_busy():
    """Test returning qbraid ID of least busy IBMQ QPU."""
    qbraid_id = ibmq_least_busy_qpu()
    assert qbraid_id[:6] == "ibm_q_"


def test_get_session_values():
    fake_user_email = "test@email.com"
    fake_id_token = "2030dksc2lkjlkjll"
    session = QbraidSession(user_email=fake_user_email, id_token=fake_id_token)
    assert session.user_email == fake_user_email
    assert session.id_token == fake_id_token


@pytest.mark.parametrize("retry_data", [("POST", 200, False, 8), ("GET", 500, True, 3)])
def test_post_forcelist_retry(retry_data):
    """Test methods for session retry checks and counters"""
    method, code, should_retry, init_retries = retry_data
    retry = PostForcelistRetry(
        total=init_retries,
        status_forcelist=STATUS_FORCELIST,
    )
    assert retry.is_retry(method, code) == should_retry
    assert retry.increment().total == init_retries - 1

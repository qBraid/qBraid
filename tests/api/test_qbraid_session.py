# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for qBraid API sessions

"""
import os

import pytest

from qbraid.api.exceptions import AuthError
from qbraid.api.retry import STATUS_FORCELIST, PostForcelistRetry
from qbraid.api.session import QbraidSession


@pytest.mark.parametrize(
    "retry_data", [("POST", 200, False, 8), ("GET", 500, True, 3), ("POST", 502, True, 4)]
)
def test_post_forcelist_retry(retry_data):
    """Test methods for session retry checks and counters"""
    method, code, should_retry, init_retries = retry_data
    retry = PostForcelistRetry(
        total=init_retries,
        status_forcelist=STATUS_FORCELIST,
    )
    assert retry.is_retry(method, code) == should_retry
    assert retry.increment().total == init_retries - 1


def test_running_in_lab():
    """Test function that checks whether qBraid Lab is running."""
    session = QbraidSession()
    assert not session._running_in_lab()


def test_check_quantum_jobs_enabled():
    """Test function that checks whether quantum jobs is enabled in qBraid Lab."""
    qbraid_envs_path = os.path.join(os.path.expanduser("~"), ".qbraid", "environments")
    proxy_dir = os.path.join(qbraid_envs_path, "qbraid_sdk_9j9sjy", "qbraid")
    proxy_file = os.path.join(proxy_dir, "proxy")
    os.makedirs(proxy_dir, exist_ok=True)
    if os.path.exists(proxy_file):
        os.remove(proxy_file)
    assert QbraidSession._qbraid_jobs_enabled() is False
    outF = open(proxy_file, "w")
    outF.writelines("active = true\n")
    outF.close()
    assert QbraidSession._qbraid_jobs_enabled() is True
    assert QbraidSession._qbraid_jobs_enabled(vendor="aws") is True
    assert QbraidSession._qbraid_jobs_enabled(vendor="ibm") is False
    os.remove(proxy_file)


def test_get_session_values():
    fake_user_email = "test@email.com"
    fake_refresh_token = "2030dksc2lkjlkjll"
    session = QbraidSession(user_email=fake_user_email, refresh_token=fake_refresh_token)
    assert session.user_email == fake_user_email
    assert session.refresh_token == fake_refresh_token


def test_convert_email_symbols():
    """Test function that converts email to username."""
    email_input = "test-format.company_org@qbraid.com"
    expected_output = "test-2dformat-2ecompany-5forg-40qbraid-2ecom"
    assert QbraidSession._convert_email_symbols(email_input) == expected_output


def test_save_config_bad_url():
    """Test that passing bad base_url to save_config raises exception."""
    session = QbraidSession()
    with pytest.raises(AuthError):
        session.save_config(base_url="bad_url")

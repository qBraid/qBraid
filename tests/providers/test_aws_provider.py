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
Unit tests for working with IBM provider

"""
import os

import pytest

from qbraid.providers.aws import BraketProvider

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of IBM storage)"


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
@pytest.mark.parametrize(
    "company,region", [("rigetti", "us-west-1"), ("ionq", "us-east-1"), ("oqc", "eu-west-2")]
)
def test_get_region_name(company, region):
    """Test getting the AWS region name."""
    provider = BraketProvider()
    fake_arn = f"arn:aws:braket:::device/qpu/{company}/device"
    assert provider._get_region_name(fake_arn) == region

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
Module for testing datetime helper functions used for getting device availability windows

"""
from datetime import datetime
from unittest.mock import patch

import pytest

from qbraid.providers.aws.device import _future_utc_datetime


# Test function
@pytest.mark.parametrize(
    "hours, minutes, seconds, expected",
    [
        (1, 0, 0, "2023-01-01T01:00:00Z"),
        (0, 30, 0, "2023-01-01T00:30:00Z"),
        (0, 0, 45, "2023-01-01T00:00:45Z"),
    ],
)
def test_future_utc_datetime(hours, minutes, seconds, expected):
    """Test calculating future utc datetime"""
    with patch("qbraid.providers.aws.device.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 0, 0, 0)
        assert _future_utc_datetime(hours, minutes, seconds) == expected

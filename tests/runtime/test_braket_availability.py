# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for Braket Availability

"""

import datetime
from unittest.mock import patch

from braket.aws.aws_device import AwsDevice
from braket.device_schema import ExecutionDay

from qbraid.runtime.braket.availability import _current_utc_datetime, next_available_time


def test_datetime_no_utc_attr():
    """Test _current_utc_datetime when datetime module does not have UTC attribute."""
    with patch("datetime.datetime") as mock_datetime:
        type(mock_datetime).UTC = datetime.timezone.utc
        mock_datetime.utcnow.return_value = "datetime without UTC"
        mock_datetime.now.return_value = "datetime with UTC"
        setattr(datetime, "UTC", datetime.timezone.utc)

        result = _current_utc_datetime()
        assert result == "datetime with UTC"


class ExecutionWindow:
    """Test class for execution window."""

    def __init__(self):
        self.windowStartHour = datetime.time(0)
        self.windowEndHour = datetime.time(23, 59, 59)
        self.executionDay = ExecutionDay.EVERYDAY


class Service:
    """Test class for braket device service."""

    def __init__(self):
        self.executionWindows = [ExecutionWindow()]


class TestProperties:
    """Test class for braket device properties."""

    def __init__(self):
        self.service = Service()


class FakeAwsDevice(AwsDevice):
    """Fake AwsDevice class for testing."""

    def __init__(self, online, available):
        self._is_available = available
        self._status = "ONLINE" if online else "OFFLINE"
        self._properties = TestProperties()

    @property
    def is_available(self):
        """Return availability of the device."""
        return self._is_available

    @is_available.setter
    def is_available(self, value):
        self._is_available = value

    @property
    def status(self):
        """Return status of the device."""
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def properties(self):
        """Return properties of the device."""
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value


def test_next_available_time_offline():
    """Test next_available_time when the device is offline."""
    device = FakeAwsDevice(online=False, available=False)
    result = next_available_time(device)
    assert result == (False, "", None)


def test_next_available_time_available():
    """Test next_available_time when the device is available."""
    device = FakeAwsDevice(online=True, available=True)
    result = next_available_time(device)
    assert result == (True, "", None)

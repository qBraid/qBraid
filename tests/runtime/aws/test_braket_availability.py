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
from unittest.mock import Mock, patch

from braket.aws.aws_device import AwsDevice
from braket.device_schema import ExecutionDay

from qbraid.runtime.aws.availability import (
    _calculate_day_factor,
    _current_utc_datetime,
    _is_day_matched,
    _is_time_matched,
    next_available_time,
)


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


def mock_execution_window(execution_day, start_hour, start_minute, end_hour, end_minute):
    """Mock execution window."""
    return Mock(
        executionDay=execution_day,
        windowStartHour=datetime.time(start_hour, start_minute),
        windowEndHour=datetime.time(end_hour, end_minute),
    )


@patch(
    "qbraid.runtime.aws.availability._current_utc_datetime",
    return_value=datetime.datetime(2024, 7, 1, 15, 30, 0, tzinfo=datetime.timezone.utc),
)
def test_next_available_random(mock_utc_datetime):  # pylint: disable=unused-argument
    """Test next_available_time."""
    execution_window = mock_execution_window(ExecutionDay.MONDAY, 16, 0, 17, 0)
    device = Mock(status="ONLINE", is_available=False)
    device.properties.service.executionWindows = [execution_window]

    result = next_available_time(device)
    assert result == (False, "00:30:00", "2024-07-01T16:00:00Z")


def test_next_available_time_no_execution_window():
    """Test next_available_time when there is no execution window."""
    device = Mock(status="ONLINE", is_available=False)
    device.properties.service.executionWindows = []

    result = next_available_time(device)
    assert result == (False, "", None)


ORDERED_DAYS = (
    ExecutionDay.MONDAY,
    ExecutionDay.TUESDAY,
    ExecutionDay.WEDNESDAY,
    ExecutionDay.THURSDAY,
    ExecutionDay.FRIDAY,
    ExecutionDay.SATURDAY,
    ExecutionDay.SUNDAY,
)


def test_is_day_matched():
    """Test _is_day_matched."""
    execution_window = mock_execution_window(ExecutionDay.EVERYDAY, 0, 0, 23, 59)
    for day in range(7):
        assert _is_day_matched(execution_window, day)

    execution_window = mock_execution_window(ExecutionDay.WEEKDAYS, 0, 0, 23, 59)
    for day in range(5):
        assert _is_day_matched(execution_window, day)
    for day in range(5, 7):
        assert not _is_day_matched(execution_window, day)

    execution_window = mock_execution_window(ExecutionDay.WEEKENDS, 0, 0, 23, 59)
    for day in range(5):
        assert not _is_day_matched(execution_window, day)
    for day in range(5, 7):
        assert _is_day_matched(execution_window, day)

    for idx, day in enumerate(ORDERED_DAYS):
        execution_window = mock_execution_window(day, 0, 0, 23, 59)
        for check_day in range(7):
            expected = check_day == idx
            assert (
                _is_day_matched(execution_window, check_day) == expected
            ), f"Failed for {day} with check day {check_day}"


def test_is_time_matched():
    """Test _is_time_matched."""
    execution_window = mock_execution_window(0, 9, 0, 17, 0)
    assert _is_time_matched(execution_window, datetime.time(10, 0))
    assert not _is_time_matched(execution_window, datetime.time(8, 0))
    assert not _is_time_matched(execution_window, datetime.time(18, 0))

    execution_window = mock_execution_window(0, 22, 0, 6, 0)
    assert _is_time_matched(execution_window, datetime.time(23, 0))
    assert _is_time_matched(execution_window, datetime.time(5, 0))
    assert not _is_time_matched(execution_window, datetime.time(7, 0))
    assert not _is_time_matched(execution_window, datetime.time(21, 0))
    assert _is_time_matched(execution_window, datetime.time(22, 0))
    assert _is_time_matched(execution_window, datetime.time(6, 0))
    assert not _is_time_matched(execution_window, datetime.time(6, 1))


@patch(
    "qbraid.runtime.aws.availability._current_utc_datetime",
    return_value=datetime.datetime(2024, 7, 10, 5, 0, 0, tzinfo=datetime.timezone.utc),
)
def test_next_available_time_midnight(mock_utc_datetime):  # pylint: disable=unused-argument
    """Test next_available_time with exec window that spans midnight."""
    execution_window = mock_execution_window(ExecutionDay.WEEKDAYS, 22, 0, 6, 0)
    device = Mock(status="ONLINE", is_available=False)
    device.properties.service.executionWindows = [execution_window]

    result = next_available_time(device)
    assert result == (True, "17:00:00", "2024-07-10T22:00:00Z")


def test_calculate_day_factor():
    """Test _calculate_day_factor."""
    day = 0
    day_factor_0 = _calculate_day_factor(day, datetime.time(0), datetime.time(0))
    assert day_factor_0 == 0

    day = 1
    day_factor_start_before_end = _calculate_day_factor(day, datetime.time(0), datetime.time(1))
    assert day_factor_start_before_end == 0

    day = 2
    day_factor_start_after_end = _calculate_day_factor(day, datetime.time(1), datetime.time(0))
    assert day_factor_start_after_end == 2

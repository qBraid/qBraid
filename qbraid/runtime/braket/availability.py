# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for calculating Amazon Braket device availability.

"""

import datetime
from typing import Optional

from braket.aws import AwsDevice
from braket.device_schema import DeviceExecutionWindow, ExecutionDay

ORDERED_DAYS = (
    ExecutionDay.MONDAY,
    ExecutionDay.TUESDAY,
    ExecutionDay.WEDNESDAY,
    ExecutionDay.THURSDAY,
    ExecutionDay.FRIDAY,
    ExecutionDay.SATURDAY,
    ExecutionDay.SUNDAY,
)


def _current_utc_datetime() -> datetime.datetime:
    """Return the current UTC datetime."""
    if not hasattr(datetime, "UTC"):  # pragma: no cover
        # backwards compatibility for Python < 3.11
        return datetime.datetime.utcnow()  # pylint: disable=no-member
    return datetime.datetime.now(datetime.timezone.utc)


def _is_day_matched(window: DeviceExecutionWindow, weekday: int):
    """Determine if the current day matches the execution day."""
    if window.executionDay == ExecutionDay.EVERYDAY:
        return True
    if window.executionDay == ExecutionDay.WEEKDAYS:
        return weekday < 5
    if window.executionDay == ExecutionDay.WEEKENDS:
        return weekday > 4
    return (
        window.executionDay in ORDERED_DAYS and ORDERED_DAYS.index(window.executionDay) == weekday
    )


def _is_time_matched(window: DeviceExecutionWindow, current_time_utc: datetime.time):
    """Determine if the current time is within the execution window."""
    if window.windowStartHour < window.windowEndHour:
        return window.windowStartHour <= current_time_utc <= window.windowEndHour
    return current_time_utc >= window.windowStartHour or current_time_utc <= window.windowEndHour


def _calculate_day_factor(day: int, start_time: datetime.time, end_time: datetime.time) -> int:
    """Calculate the day factor based on the current day and execution window."""
    if day == 0:
        return day
    if start_time < end_time:
        return day - 1
    return day


def _calculate_future_time(
    available_time: int, current_datetime_utc: datetime.datetime
) -> tuple[str, str]:
    """
    Calculates future time from the current datetime in UTC and the available time in seconds.

    Args:
        available_time (int): Available time in seconds.
        current_datetime_utc (datetime.datetime): Current datetime in UTC.

    Returns:
        tuple: A tuple containing available time in "HH:MM:SS" format and
               future UTC datetime in ISO 8601 format "YYYY-MM-DDTHH:MM:SSZ".
    """
    hours = available_time // 3600
    minutes = (available_time // 60) % 60
    seconds = available_time % 60
    available_time_hms = f"{hours:02}:{minutes:02}:{seconds:02}"

    time_delta = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    future_time = current_datetime_utc + time_delta
    utc_datetime_str = future_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    return available_time_hms, utc_datetime_str


def next_available_time(device: AwsDevice) -> tuple[bool, str, Optional[str]]:
    """Returns hr/min/sec until device is next available, or empty string if device is offline."""

    is_available_result = False
    available_time = None

    if device.status != "ONLINE":
        return False, "", None

    if device.is_available:
        return True, "", None

    day = 0

    current_datetime_utc = _current_utc_datetime()
    for execution_window in device.properties.service.executionWindows:
        weekday = current_datetime_utc.weekday()
        current_time_utc = current_datetime_utc.time().replace(microsecond=0)

        if (
            execution_window.windowEndHour < execution_window.windowStartHour
            and current_time_utc < execution_window.windowEndHour
        ):
            weekday = (weekday - 1) % 7

        matched_day = _is_day_matched(execution_window, weekday)
        matched_time = _is_time_matched(execution_window, current_time_utc)

        if execution_window.executionDay in ORDERED_DAYS:
            day = (ORDERED_DAYS.index(execution_window.executionDay) - weekday) % 7

        start_time = execution_window.windowStartHour
        end_time = current_time_utc
        day_factor = _calculate_day_factor(day, start_time, end_time)

        td = datetime.timedelta(
            hours=start_time.hour,
            minutes=start_time.minute,
            seconds=start_time.second,
        ) - datetime.timedelta(
            hours=end_time.hour, minutes=end_time.minute, seconds=end_time.second
        )
        days_seconds = 86400 * day_factor
        available_time_secs = td.seconds + days_seconds

        if available_time is None or available_time_secs < available_time:
            available_time = available_time_secs

        is_available_result = is_available_result or (matched_day and matched_time)

    if available_time is None:
        return is_available_result, "", None

    available_time_hms, utc_datetime_str = _calculate_future_time(
        available_time, current_datetime_utc
    )
    return is_available_result, available_time_hms, utc_datetime_str

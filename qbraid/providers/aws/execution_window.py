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
Module for retrieving Braket devices availability information.

"""
from datetime import datetime, timedelta

from braket.aws import AwsDevice
from braket.device_schema import DeviceExecutionWindow, ExecutionDay


# Function to check if current UTC time is within the execution window
def is_within_execution_window(execution_window: DeviceExecutionWindow) -> bool:
    """Returns True if the current UTC time is within the execution window, False otherwise."""
    current_utc = datetime.utcnow()
    current_day = current_utc.strftime("%A")
    current_time = current_utc.time()

    # pylint: disable=too-many-boolean-expressions
    # Check if the current day matches the execution day
    if (
        execution_window.executionDay == ExecutionDay.EVERYDAY
        or (
            execution_window.executionDay == ExecutionDay.WEEKDAYS
            and current_day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        )
        or (
            execution_window.executionDay == ExecutionDay.WEEKENDS
            and current_day in ["Saturday", "Sunday"]
        )
        or execution_window.executionDay.value == current_day
    ):
        # Check if the current time is within the execution window
        return execution_window.windowStartHour <= current_time <= execution_window.windowEndHour
    return False


def next_availability(execution_window: DeviceExecutionWindow) -> (bool, datetime):
    """Returns availability status and next change in availability status (UTC datetime)."""
    current_utc = datetime.utcnow()
    current_day = current_utc.strftime("%A")

    # Helper function to create a datetime from today with specified hour
    def create_datetime(time_obj) -> datetime:
        return datetime(current_utc.year, current_utc.month, current_utc.day, time_obj.hour)

    # Helper function to add a day considering weekdays and weekends
    def add_day(date: datetime, day_type: str) -> datetime:
        if day_type == "weekday":
            return date + timedelta(days=1 if date.weekday() < 4 else 3)
        if day_type == "weekend":
            return date + timedelta(days=1 if date.weekday() == 5 else 6 - date.weekday())
        return date + timedelta(days=1)

    # pylint: disable=too-many-boolean-expressions
    # Check if the current day matches the execution day
    if (
        execution_window.executionDay == ExecutionDay.EVERYDAY
        or (
            execution_window.executionDay == ExecutionDay.WEEKDAYS
            and current_day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        )
        or (
            execution_window.executionDay == ExecutionDay.WEEKENDS
            and current_day in ["Saturday", "Sunday"]
        )
        or execution_window.executionDay.value == current_day.upper()
    ):
        window_start = create_datetime(execution_window.windowStartHour)
        window_end = create_datetime(execution_window.windowEndHour)
        if window_start <= current_utc <= window_end:
            # Currently within execution window
            return True, window_end
        if current_utc < window_start:
            # Before today's execution window
            return False, window_start

    # After today's execution window or on a non-execution day
    next_day = add_day(
        current_utc,
        "weekday" if execution_window.executionDay == ExecutionDay.WEEKDAYS else "weekend",
    )
    next_window_start = create_datetime(execution_window.windowStartHour).replace(
        year=next_day.year, month=next_day.month, day=next_day.day
    )
    return False, next_window_start


def is_available(device: AwsDevice) -> bool:
    """Returns true if the device is currently available.

    Returns:
        bool: Return if the device is currently available.

    """
    if device.status != "ONLINE":
        return False, None

    next_available_datetime = None
    for execution_window in device.properties.service.executionWindows:
        is_available_result = is_within_execution_window(execution_window)
        _, future_utc_datetime = next_availability(execution_window)
        if is_available_result:
            return is_available_result, future_utc_datetime

        if next_available_datetime is None or future_utc_datetime < next_available_datetime:
            next_available_datetime = future_utc_datetime

    return False, next_available_datetime

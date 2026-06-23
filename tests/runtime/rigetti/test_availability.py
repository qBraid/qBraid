# Copyright 2026 qBraid
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

# pylint: disable=protected-access,possibly-used-before-assignment

"""Unit tests for the Rigetti availability module."""

from __future__ import annotations

import datetime
import importlib.util
from unittest.mock import MagicMock

import pytest

from qbraid.runtime.enums import DeviceStatus

rigetti_deps_found = (
    importlib.util.find_spec("pyquil") is not None
    and importlib.util.find_spec("qcs_sdk") is not None
)
pytestmark = pytest.mark.skipif(not rigetti_deps_found, reason="Rigetti dependencies not installed")

if rigetti_deps_found:
    from qbraid.runtime.rigetti import availability


def _build_ical(*windows: tuple[datetime.datetime, datetime.datetime]) -> str:
    """Build a maintenance iCalendar from one or more ``(start, end)`` windows."""
    fmt = "%Y%m%dT%H%M%SZ"
    events = ""
    for i, (start, end) in enumerate(windows):
        start_utc = start.astimezone(datetime.timezone.utc).strftime(fmt)
        end_utc = end.astimezone(datetime.timezone.utc).strftime(fmt)
        events += (
            f"BEGIN:VEVENT\r\nUID:evt-{i}@qcs\r\nSUMMARY:Maintenance\r\n"
            f"DTSTART:{start_utc}\r\nDTEND:{end_utc}\r\nEND:VEVENT\r\n"
        )
    return f"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\n{events}END:VCALENDAR\r\n"


def _mock_device(status: DeviceStatus, ical: str = "") -> MagicMock:
    """A mock RigettiDevice exposing status() and maintenance_calendar()."""
    device = MagicMock()
    device.status.return_value = status
    device.maintenance_calendar.return_value = ical
    return device


# A maintenance calendar with a single fixed window: 2026-06-23 08:00–12:00 UTC.
FIXED_ICAL = _build_ical(
    (
        datetime.datetime(2026, 6, 23, 8, 0, tzinfo=datetime.timezone.utc),
        datetime.datetime(2026, 6, 23, 12, 0, tzinfo=datetime.timezone.utc),
    )
)


# ===========================================================================
# Pure helpers
# ===========================================================================


class TestHelpers:
    """Tests for the standalone availability helpers."""

    @pytest.mark.parametrize(
        "seconds,expected",
        [(0, "00:00:00"), (59, "00:00:59"), (3661, "01:01:01"), (45296, "12:34:56")],
    )
    def test_format_duration(self, seconds: int, expected: str) -> None:
        """Durations are rendered as zero-padded HH:MM:SS."""
        assert availability._format_duration(seconds) == expected

    def test_as_utc_datetime_naive_assumed_utc(self) -> None:
        """A naive datetime is treated as UTC."""
        naive = datetime.datetime(2026, 6, 23, 9, 0)
        result = availability._as_utc_datetime(naive)
        assert result == datetime.datetime(2026, 6, 23, 9, 0, tzinfo=datetime.timezone.utc)

    def test_as_utc_datetime_converts_to_utc(self) -> None:
        """An aware datetime is converted to UTC."""
        tz = datetime.timezone(datetime.timedelta(hours=5))
        aware = datetime.datetime(2026, 6, 23, 14, 0, tzinfo=tz)
        result = availability._as_utc_datetime(aware)
        assert result == datetime.datetime(2026, 6, 23, 9, 0, tzinfo=datetime.timezone.utc)

    def test_as_utc_datetime_date_to_midnight_utc(self) -> None:
        """A plain date maps to midnight UTC."""
        result = availability._as_utc_datetime(datetime.date(2026, 6, 23))
        assert result == datetime.datetime(2026, 6, 23, 0, 0, tzinfo=datetime.timezone.utc)


# ===========================================================================
# is_in_maintenance
# ===========================================================================


class TestIsInMaintenance:
    """Tests for availability.is_in_maintenance."""

    def test_true_inside_window(self) -> None:
        """now inside the published window returns True."""
        now = datetime.datetime(2026, 6, 23, 9, 0, tzinfo=datetime.timezone.utc)
        assert availability.is_in_maintenance(FIXED_ICAL, now) is True

    def test_false_outside_window(self) -> None:
        """now outside the published window returns False."""
        now = datetime.datetime(2026, 6, 23, 15, 0, tzinfo=datetime.timezone.utc)
        assert availability.is_in_maintenance(FIXED_ICAL, now) is False

    def test_false_when_empty_calendar(self) -> None:
        """An empty calendar means the device is never under maintenance."""
        assert availability.is_in_maintenance("") is False


# ===========================================================================
# next_available_time
# ===========================================================================


class TestNextAvailableTime:
    """Tests for availability.next_available_time."""

    def test_offline_returns_unavailable_no_eta(self) -> None:
        """An OFFLINE device is unavailable with no known return time."""
        device = _mock_device(DeviceStatus.OFFLINE)
        assert availability.next_available_time(device) == (False, "", None)
        device.maintenance_calendar.assert_not_called()

    def test_online_returns_available(self) -> None:
        """An ONLINE device is available now with no pending switch."""
        device = _mock_device(DeviceStatus.ONLINE)
        assert availability.next_available_time(device) == (True, "", None)
        device.maintenance_calendar.assert_not_called()

    def test_unavailable_returns_time_until_window_end(self) -> None:
        """An in-progress window yields time remaining until it ends."""
        now = availability._current_utc_datetime()
        start = now - datetime.timedelta(minutes=30)
        end = now + datetime.timedelta(minutes=30)
        device = _mock_device(DeviceStatus.UNAVAILABLE, _build_ical((start, end)))

        is_available, remaining, switch = availability.next_available_time(device)

        assert is_available is False
        assert switch is not None
        assert abs((switch - end).total_seconds()) < 1
        # ~30 minutes remaining (allow a small clock delta).
        assert 29 * 60 <= int((switch - now).total_seconds()) <= 30 * 60
        assert remaining.startswith(("00:29", "00:30"))

    def test_unavailable_merges_contiguous_windows(self) -> None:
        """Back-to-back windows extend the maintenance block to the later end."""
        now = availability._current_utc_datetime()
        first = (now - datetime.timedelta(minutes=10), now + datetime.timedelta(minutes=10))
        second = (now + datetime.timedelta(minutes=10), now + datetime.timedelta(minutes=40))
        device = _mock_device(DeviceStatus.UNAVAILABLE, _build_ical(first, second))

        _, _, switch = availability.next_available_time(device)

        assert switch is not None
        assert abs((switch - second[1]).total_seconds()) < 1

    def test_unavailable_with_empty_calendar_has_no_eta(self) -> None:
        """UNAVAILABLE but no published calendar yields no return time."""
        device = _mock_device(DeviceStatus.UNAVAILABLE, "")
        assert availability.next_available_time(device) == (False, "", None)

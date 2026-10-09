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

"""
Module for calculating Rigetti QCS device availability from the maintenance
calendar published by the QCS REST API.

"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import icalendar
import recurring_ical_events
import requests

from qbraid.runtime.enums import DeviceStatus

if TYPE_CHECKING:
    from .device import RigettiDevice

# Bounded horizon when expanding (possibly recurring) maintenance events to
# find the end of the maintenance block currently in progress. This prevents
# unbounded recurrence expansion for indefinitely-repeating rules.
_MAINTENANCE_HORIZON = datetime.timedelta(weeks=1)

# Hosts a linked maintenance feed may be fetched from. This runs server-side too, so a
# link anywhere else (an internal address, say) is refused rather than requested.
_FEED_HOSTS = frozenset({"calendar.google.com"})


def _current_utc_datetime() -> datetime.datetime:
    """Return the current UTC datetime."""
    return datetime.datetime.now(datetime.timezone.utc)


def follow_feed_link(ical: str, timeout: float) -> str:
    """Return ``ical``, or the calendar it links to when it is an ``https`` URL.

    QCS publishes some processors' maintenance (Cepheus-1-108Q's, for one) as a link to a
    Google Calendar feed rather than inline. The feed is public, so it is fetched without
    the QCS bearer token, which must not be sent to a third party.

    Raises:
        ValueError: If the link is to a host outside ``_FEED_HOSTS``, or redirects.
        requests.RequestException: If the linked feed cannot be fetched.
    """
    url = ical.strip()
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return ical
    if parsed.hostname not in _FEED_HOSTS:
        raise ValueError(f"Refusing to fetch a maintenance feed from {parsed.hostname!r}.")
    response = requests.get(
        url, headers={"Accept": "text/calendar"}, timeout=timeout, allow_redirects=False
    )
    if response.is_redirect:
        raise ValueError("Refusing to follow a redirect from the maintenance feed.")
    response.raise_for_status()
    return response.text


def _parse_calendar(ical_text: str) -> icalendar.Calendar | None:
    """Parse iCalendar text into a calendar, or ``None`` when empty."""
    if not ical_text or not ical_text.strip():
        return None
    return icalendar.Calendar.from_ical(ical_text)


def _as_utc_datetime(value: Any) -> datetime.datetime | None:
    """Normalise an iCal date/datetime to a timezone-aware UTC datetime."""
    # datetime is a subclass of date, so check it first.
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)
    if isinstance(value, datetime.date):
        return datetime.datetime(value.year, value.month, value.day, tzinfo=datetime.timezone.utc)
    return None


def _format_duration(seconds: int) -> str:
    """Format a non-negative duration in seconds as ``HH:MM:SS``."""
    hours = seconds // 3600
    minutes = (seconds // 60) % 60
    secs = seconds % 60
    return f"{hours:02}:{minutes:02}:{secs:02}"


def is_in_maintenance(ical_text: str, now: datetime.datetime | None = None) -> bool:
    """Return ``True`` if a maintenance window covers ``now``.

    Args:
        ical_text: The raw maintenance iCalendar (RFC 5545). An empty string
            means no maintenance is scheduled.
        now: The instant to test. Defaults to the current UTC time.
    """
    now = now or _current_utc_datetime()
    calendar = _parse_calendar(ical_text)
    if calendar is None:
        return False
    return bool(recurring_ical_events.of(calendar).at(now))


def _maintenance_block_end(
    calendar: icalendar.Calendar,
    now: datetime.datetime,
    horizon: datetime.timedelta = _MAINTENANCE_HORIZON,
) -> datetime.datetime | None:
    """Return the end of the contiguous maintenance block covering ``now``.

    Adjacent or overlapping maintenance windows are merged so that the result
    is the moment the device next leaves maintenance. Returns ``None`` if no
    window covers ``now`` within ``horizon``.
    """
    windows: list[tuple[datetime.datetime, datetime.datetime]] = []
    for event in recurring_ical_events.of(calendar).between(now, now + horizon):
        start = _as_utc_datetime(event.start)
        end = _as_utc_datetime(event.end)
        if start is not None and end is not None:
            windows.append((start, end))
    windows.sort(key=lambda window: window[0])

    block_end: datetime.datetime | None = None
    for start, end in windows:
        if start <= now < end:
            # Window currently in progress.
            block_end = end if block_end is None else max(block_end, end)
        elif block_end is not None and start <= block_end:
            # Adjacent/overlapping window extends the maintenance block.
            block_end = max(block_end, end)
        elif block_end is not None and start > block_end:
            # Gap reached; the contiguous maintenance block has ended.
            break
    return block_end


def next_available_time(
    device: RigettiDevice,
) -> tuple[bool, str, datetime.datetime | None]:
    """Provide the device's maintenance-based availability.

    Mirrors :func:`qbraid.runtime.aws.availability.next_available_time`: it
    reports whether the device is available now, the time remaining until the
    next change in availability, and the UTC datetime of that change.

    For Rigetti, (un)availability is derived from the QCS maintenance
    calendar: the device is available unless a maintenance window is in
    progress, during which the QCS gateway queues jobs instead of executing
    them.

    Returns:
        tuple[bool, str, Optional[datetime.datetime]]:
            - whether the device is available now,
            - ``HH:MM:SS`` until the device next becomes available (empty when
              already available or when the return time is unknown),
            - the future UTC datetime at which the device becomes available
              (``None`` when already available or unknown).
    """
    status = device.status()
    if status == DeviceStatus.OFFLINE:
        return False, "", None
    if status == DeviceStatus.ONLINE:
        return True, "", None

    # status == UNAVAILABLE: a maintenance window is currently in progress.
    now = _current_utc_datetime()
    calendar = _parse_calendar(device.maintenance_calendar())
    if calendar is None:
        return False, "", None

    block_end = _maintenance_block_end(calendar, now)
    if block_end is None:
        return False, "", None

    seconds = max(0, int((block_end - now).total_seconds()))
    return False, _format_duration(seconds), block_end

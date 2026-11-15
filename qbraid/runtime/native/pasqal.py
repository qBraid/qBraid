# Copyright 2025 qBraid
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
Checks a Pulser sequence against the Pasqal QPU it is submitted to, before it is submitted.

Pasqal moves every QPU sequence onto the QPU's own Pulser ``Device`` and validates it there.
A sequence built on another device, such as Pulser's ``AnalogDevice``, is rejected after it has
been queued. Running the same checks here reports the reason at once.

The check never stands between a user and Pasqal when it cannot be sure: if Pasqal's specs
cannot be read, the sequence is submitted unchecked, and Pasqal validates it as before. The
specs are Pasqal's public ones, which may lag a recalibration by up to the cache lifetime; a
user who believes a rejection is wrong can skip the check with
``device.set_options(validate=0)``.

"""
from __future__ import annotations

import contextlib
import threading
import time
import warnings
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import requests

from qbraid._logging import logger

if TYPE_CHECKING:
    import pulser

PASQAL_PUBLIC_SPECS_URL = "https://apis.pasqal.cloud/core-fast/api/v1/devices/public-specs"

# Pasqal's QPU specs change with recalibrations, so fetched devices are reused for a while
# rather than for the life of the process. A failed fetch is remembered for a shorter time, so
# an unreachable endpoint costs one short wait, not one per submitted program.
_SPECS_TTL_S = 600.0
_FAILURE_TTL_S = 60.0
_SPECS_TIMEOUT_S = (3.0, 5.0)  # connect, read

# Specs older than this are dropped rather than reused while Pasqal's endpoint is unreachable.
_MAX_STALE_S = 2 * _SPECS_TTL_S

_lock = threading.Lock()
_cache: dict[str, Any] = {"devices": {}, "fresh_until": 0.0, "fetched_at": 0.0, "refreshing": False}

# warnings.catch_warnings swaps the process-wide filter list, so overlapping blocks in different
# threads can restore each other's temporary filter and leave every warning silenced. Pulser's
# own warnings are suppressed one block at a time.
_warnings_lock = threading.Lock()


@contextlib.contextmanager
def _quiet() -> Iterator[None]:
    """Suppress Pulser's warnings (deprecations, Rydberg-level notes) for one call."""
    with _warnings_lock, warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


def _reset_cache() -> None:
    """Forget the fetched specs. Used by tests."""
    with _lock:
        _cache.update(devices={}, fresh_until=0.0, fetched_at=0.0, refreshing=False)


def pasqal_device_type(device_id: str) -> str:
    """Pasqal's device type for a qBraid device ID, e.g. ``FRESNEL_CAN1``."""
    return device_id.split(":")[-1].upper().replace("-", "_")


def _fetch_public_devices() -> dict[str, pulser.devices.Device]:
    """Pasqal's QPU devices by device type, from its public specs endpoint.

    An entry that cannot be read, for example one written for a newer Pulser, is skipped
    rather than discarding the devices that can.
    """
    # pylint: disable-next=import-outside-toplevel
    from pulser.json.abstract_repr.deserializer import deserialize_device

    response = requests.get(PASQAL_PUBLIC_SPECS_URL, timeout=_SPECS_TIMEOUT_S)
    response.raise_for_status()
    devices = {}
    for entry in response.json()["data"]:
        try:
            with _quiet():
                devices[entry["device_type"]] = deserialize_device(entry["specs"])
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.info("Skipping Pasqal specs entry %s: %s", entry.get("device_type"), err)
    return devices


def get_pasqal_qpu_device(device_type: str) -> pulser.devices.Device | None:
    """The Pulser ``Device`` Pasqal validates ``device_type`` sequences against.

    Returns ``None`` when no specs have been read for it. The network call is made outside
    the lock, and only by one caller at a time: others use the last specs read, if any.
    """
    with _lock:
        now = time.monotonic()
        if now < _cache["fresh_until"] or _cache["refreshing"]:
            return _cache["devices"].get(device_type)
        _cache["refreshing"] = True

    devices: dict[str, Any] | None = None
    try:
        devices = _fetch_public_devices()
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.info("Pasqal specs unavailable; using the last ones read, if any (%s)", err)
    finally:
        with _lock:
            _cache["refreshing"] = False
            now = time.monotonic()
            if devices is not None:
                _cache.update(devices=devices, fetched_at=now, fresh_until=now + _SPECS_TTL_S)
            else:
                _cache["fresh_until"] = now + _FAILURE_TTL_S
                if now - _cache["fetched_at"] > _MAX_STALE_S:
                    _cache["devices"] = {}

    with _lock:
        return _cache["devices"].get(device_type)


def _reason(err: Exception) -> str:
    """The error's message, or its type when Pulser raised it without one."""
    return str(err).strip() or type(err).__name__


def validate_pulser_for_pasqal_qpu(sequence: pulser.Sequence, device_id: str) -> None:
    """Raises a ValueError if Pasqal's QPU would reject ``sequence`` at validation.

    Checks, against the QPU's own device: that a fixed register is defined from a layout when
    the QPU requires one, and meets its layout, filling and distance rules; and, for a sequence
    built on another device, that it can be moved onto the QPU, which checks its register,
    channels, pulses and duration. A sequence already built on the QPU's device was validated
    by Pulser as it was built. The user's sequence is not modified.
    """
    # pylint: disable-next=import-outside-toplevel
    from pulser import Sequence

    device_type = pasqal_device_type(device_id)
    target = get_pasqal_qpu_device(device_type)
    if target is None:
        return

    guidance = (
        f"Build the sequence on Pasqal's {device_type} Pulser device (its specs are public at "
        f"{PASQAL_PUBLIC_SPECS_URL}; load them with pulser's deserialize_device) and define the "
        "register from one of its calibrated layouts (device.calibrated_register_layouts)."
    )

    if not sequence.is_register_mappable():
        register = sequence.register
        if target.requires_layout and register.layout is None:
            raise ValueError(
                f"{device_type} requires the sequence's register to be defined from a "
                f"RegisterLayout. {guidance}"
            )
        try:
            with _quiet():
                Sequence(register, target)
        except Exception as err:  # pylint: disable=broad-exception-caught
            raise ValueError(
                f"The sequence's register is not valid on {device_type}: {_reason(err)} "
                f"{guidance}"
            ) from err

    if sequence.device.name == target.name:
        return
    # Non-strict, as Pasqal moves sequences between devices: a strict match would also reject
    # sequences that differ only in device properties Pasqal does not require to match.
    move = getattr(sequence, "with_new_device", None) or sequence.switch_device
    try:
        with _quiet():
            move(target, strict=False)
    except Exception as err:  # pylint: disable=broad-exception-caught
        raise ValueError(
            f"The sequence is not valid on {device_type}: {_reason(err)} {guidance}"
        ) from err

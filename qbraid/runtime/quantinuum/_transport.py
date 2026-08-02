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
Transport-level hardening shared by the Quantinuum device and job classes.

qnexus builds a single module-level ``httpx.Client`` with ``timeout=None`` and
raises its own exception types instead of letting httpx surface HTTP errors.
Both choices need compensating for before the provider is safe to run inside a
server process:

* an unbounded client means any qnexus call can pin the calling thread forever
  on a hung socket, which starves shared executors;
* because qnexus checks status codes by hand, a NEXUS 502/503 never appears as
  an ``httpx.HTTPStatusError``, so naive transport-level retries miss the most
  common cloud blip.

"""
from __future__ import annotations

import math
import os
import random
import time
from typing import Callable, TypeVar

from qbraid._logging import logger
from qbraid.runtime.exceptions import QbraidRuntimeError

_T = TypeVar("_T")

#: Per-request bound applied to the shared qnexus HTTP client.
DEFAULT_HTTP_TIMEOUT_SECONDS = 60.0

#: Gateway-class responses that are worth repeating. Anything else (400s, and
#: 500s that indicate a rejected program rather than an unavailable upstream)
#: is a real failure and is raised immediately.
RETRYABLE_STATUS_CODES = frozenset({502, 503, 504})

_HTTP_TIMEOUT_ENV = "QUANTINUUM_NEXUS_HTTP_TIMEOUT"


class QuantinuumDeviceError(QbraidRuntimeError):
    """Exception raised by QuantinuumDevice."""


def positive_float_env(name: str, default: float) -> float:
    """Read a positive number of seconds from the environment.

    Fails loudly rather than letting a typo degrade into a confusing runtime
    error: ``FOO=abc`` would otherwise raise a bare ``ValueError`` that never
    names the variable, and ``FOO=0`` would silently make every call expire.

    ``nan`` and ``inf`` are rejected explicitly. ``float()`` accepts both, and
    every ordering comparison against NaN is false, so a bare ``value <= 0``
    check waves it through into httpx and qnexus to fail later somewhere with
    no connection to the variable that caused it.

    Args:
        name: Environment variable to read.
        default: Value to use when the variable is unset.

    Returns:
        The resolved number of seconds.

    Raises:
        QuantinuumDeviceError: If the variable is set but is not a finite
            positive number.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as err:
        raise QuantinuumDeviceError(f"{name} must be a number of seconds, got {raw!r}.") from err
    if not math.isfinite(value):
        raise QuantinuumDeviceError(f"{name} must be a finite number of seconds, got {raw!r}.")
    if value <= 0:
        raise QuantinuumDeviceError(f"{name} must be positive, got {value}.")
    return value


def bounded_int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    """Read an integer from the environment, validating it against a range.

    Args:
        name: Environment variable to read.
        default: Value to use when the variable is unset.
        minimum: Smallest accepted value, inclusive.
        maximum: Largest accepted value, inclusive.

    Returns:
        The resolved integer.

    Raises:
        QuantinuumDeviceError: If the variable is set but is not an integer
            within ``[minimum, maximum]``.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as err:
        raise QuantinuumDeviceError(f"{name} must be an integer, got {raw!r}.") from err
    if not minimum <= value <= maximum:
        raise QuantinuumDeviceError(f"{name} must be between {minimum} and {maximum}, got {value}.")
    return value


def ensure_bounded_client() -> None:
    """Give the shared qnexus HTTP client a per-request timeout.

    qnexus constructs ``httpx.Client(..., timeout=None)`` once per process, so
    every qnexus call inherits an unbounded socket. A single hung connection
    then holds the calling thread indefinitely; inside ``qbraid-runtime-api``
    that thread belongs to a shared executor, and enough of them starve job
    submission and status polling alike.

    The bound is a per-request one, not an overall deadline, so it does not cap
    how long a job may take: ``qnx.jobs.wait_for`` waits over a websocket and
    falls back to short polling requests, both of which stay well inside it.

    An explicitly set ``QUANTINUUM_NEXUS_HTTP_TIMEOUT`` always wins. Otherwise
    the default is applied only when the client is still unbounded, so a caller
    that configured its own timeout keeps it.
    """
    # pylint: disable-next=import-outside-toplevel
    import httpx

    # pylint: disable-next=import-outside-toplevel
    import qnexus as qnx

    client = qnx.client.get_nexus_client()
    explicit = os.getenv(_HTTP_TIMEOUT_ENV) is not None
    unbounded = all(
        component is None
        for component in (
            client.timeout.connect,
            client.timeout.read,
            client.timeout.write,
            client.timeout.pool,
        )
    )
    if not explicit and not unbounded:
        return
    seconds = positive_float_env(_HTTP_TIMEOUT_ENV, DEFAULT_HTTP_TIMEOUT_SECONDS)
    client.timeout = httpx.Timeout(seconds)


def _retryable_exception_types() -> tuple[type[Exception], ...]:
    """Return the exception types worth inspecting for a retry."""
    # pylint: disable-next=import-outside-toplevel
    import httpx

    # pylint: disable-next=import-outside-toplevel
    import qnexus.exceptions as qnx_exc

    return (
        httpx.TransportError,
        ConnectionError,
        qnx_exc.ResourceCreateFailed,
        qnx_exc.ResourceFetchFailed,
    )


def _is_retryable(err: Exception) -> bool:
    """Return whether ``err`` represents a transient NEXUS failure.

    Connection-level errors always are. qnexus's own resource errors carry the
    HTTP status code, so they are retried only for gateway-class responses; a
    400 or a rejected program must surface immediately.
    """
    status_code = getattr(err, "status_code", None)
    if status_code is None:
        return True
    return status_code in RETRYABLE_STATUS_CODES


def retry_transient(fn: Callable[[], _T], attempts: int = 3, base_delay: float = 0.5) -> _T:
    """Run ``fn``, retrying with jittered backoff on transient NEXUS failures.

    Only used for stages that are safe to repeat (uploads, compile dispatch,
    read-only fetches). Never wrap ``start_execute_job`` in this: a disconnect
    after the server accepted the request would double-submit the job.

    The backoff is deliberately short and jittered. Sleeping holds the calling
    thread, and the failure this guards against is a NEXUS blip that hits every
    concurrent submit at once, so a long lockstep sleep would add pool pressure
    in exactly the scenario it is meant to survive. With the defaults the worst
    case adds under two seconds.

    Args:
        fn: Zero-argument callable to run.
        attempts: Total number of tries, including the first.
        base_delay: Backoff base in seconds.

    Returns:
        Whatever ``fn`` returns.

    Raises:
        ValueError: If ``attempts`` is less than one.
    """
    if attempts < 1:
        raise ValueError(f"attempts must be at least 1, got {attempts}.")

    retryable = _retryable_exception_types()
    for attempt in range(attempts):
        try:
            return fn()
        except retryable as err:
            if attempt == attempts - 1 or not _is_retryable(err):
                raise
            window = base_delay * (2**attempt)
            delay = window / 2 + random.uniform(0, window / 2)  # nosec B311
            logger.warning("Transient NEXUS error (%s); retrying in %.2fs", err, delay)
            time.sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover

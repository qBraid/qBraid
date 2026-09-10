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
Exceptions raised by the QDI runtime provider.

Defined in their own module so they carry a public, importable path in
tracebacks and docs, and so ``client`` can use them without a circular
import through ``device``.

"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from qbraid.runtime.exceptions import QbraidRuntimeError

from .protocol import QdiStatus


class QdiError(QbraidRuntimeError):
    """A QDI operation failed with a :class:`QdiStatus` code.

    Attributes:
        status: The QDI status code.
        detail: The transport's original message, when it had one.
        operation: The QDI verb that failed (``"discover"``, ``"send"``, ...).
    """

    def __init__(
        self, status: QdiStatus, detail: str | None = None, *, operation: str | None = None
    ):
        self.status = status
        self.detail = detail
        self.operation = operation
        prefix = f"QDI {operation} failed" if operation else "QDI operation failed"
        super().__init__(f"{prefix} with {status.name}" + (f": {detail}" if detail else "."))


class QdiDeviceError(QbraidRuntimeError):
    """Exception raised by QdiDevice."""


class QdiJobError(QbraidRuntimeError):
    """Class for errors raised while processing a QDI job."""


def qdi_error_from(exc: BaseException, operation: str) -> QdiError:
    """Translate whatever a QDI client raised into a :class:`QdiError`.

    Clients built on the reference ``qdi.h`` shape (qdi-demo, qdi-oqtopus)
    raise their own exception types carrying the status as ``status`` or
    ``code``; that value is kept. A transport-level failure with no status
    (socket error, timeout) maps to ``ERROR_CONNECTION_FAILED``, and anything
    else to ``ERROR_UNKNOWN``, so no failure is dropped on the floor.
    """
    if isinstance(exc, QdiError):
        return exc
    raw = getattr(exc, "status", None)
    if raw is None:
        raw = getattr(exc, "code", None)
    try:
        status = QdiStatus(int(raw))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        status = (
            QdiStatus.ERROR_CONNECTION_FAILED
            if isinstance(exc, (OSError, TimeoutError))
            else QdiStatus.ERROR_UNKNOWN
        )
    return QdiError(status, str(exc) or None, operation=operation)


@contextmanager
def qdi_call(operation: str) -> Iterator[None]:
    """Wrap a single client call so its failure surfaces as :class:`QdiError`."""
    try:
        yield
    except QdiError:
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise qdi_error_from(exc, operation) from exc

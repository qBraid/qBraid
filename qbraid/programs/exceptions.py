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
Module defining exceptions for errors raised by qBraid.

"""
from typing import Any, Optional

from qbraid_core._import import LazyLoader

from qbraid.exceptions import QbraidError

registry = LazyLoader("registry", globals(), "qbraid.programs.registry")


class QasmError(QbraidError):
    """For errors raised while processing OpenQASM programs."""


class TransformError(QbraidError):
    """Base class for errors raised during qBraid transform processes."""


class PackageValueError(QbraidError):
    """Class for errors raised due to unsupported quantum frontend package"""

    def __init__(self, package: str):
        msg = (
            f"Quantum frontend module '{package}' is not supported.\n"
            f"Frontends supported by qBraid are: {registry.QPROGRAM_ALIASES}"
        )
        super().__init__(msg)


class ProgramTypeError(QbraidError):
    """Exception raised for errors encountered with unsupported quantum programs.

    Attributes:
        program (Optional[Any]): The program that caused the error, default is None.
        message (Optional[str]): Explanation of the error. If None, a default error message
                                 is generated based on the provided program.
    """

    def __init__(self, program: Optional[Any] = None, message: Optional[str] = None):
        self.program = program
        self.message = message
        super().__init__(self.generate_message())

    def generate_message(self) -> str:
        """Generate an error message based on the input."""
        if self.message is not None:
            return self.message
        if self.program is not None:
            return f"Quantum program of type '{type(self.program)}' is not supported."
        return "Unsupported quantum program type."


class ValidationError(ProgramTypeError):
    """Custom exception for validation errors in program types."""


class ProgramLoaderError(QbraidError):
    """Raised when an error occurs while loading a quantum program."""


def _find_offending_token(err: BaseException) -> Optional[Any]:
    """Return the first ANTLR token with a line and column chained to ``err``, if any."""
    seen: set[int] = set()
    stack: list[Any] = [err]
    while stack:
        current = stack.pop()
        if not isinstance(current, BaseException) or id(current) in seen:
            continue
        seen.add(id(current))
        token = getattr(current, "offendingToken", None)
        if token is not None and hasattr(token, "line") and hasattr(token, "column"):
            return token
        # BailErrorStrategy wraps the RecognitionException in ParseCancellationException.args
        stack.extend(current.args)
        stack.extend([current.__context__, current.__cause__])
    return None


def describe_error(err: BaseException) -> str:
    """Return ``str(err)``, recovering the parse location when the message is empty.

    The ANTLR-based OpenQASM parsers (``openqasm3`` and Braket's copy of it) raise
    ``QASM3ParsingError()`` with no message and leave the offending token on the chained
    ANTLR exception. When ``str(err)`` is empty or ends in a dangling colon, that token's
    position is appended, with a 1-based column.
    """
    message = str(err).strip()
    if message and not message.endswith(":"):
        return message
    token = _find_offending_token(err)
    if token is None:
        return message or type(err).__name__
    text = getattr(token, "text", None)
    where = f"at line {token.line}, column {token.column + 1}"
    if text is None or text == "<EOF>":
        detail = f"syntax error: unexpected end of program {where}"
    else:
        detail = f"syntax error near '{text}' {where}"
    return f"{message} {detail}" if message else detail

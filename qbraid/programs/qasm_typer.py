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
Module providing type checking for OpenQASM programs.

"""
from typing import Optional

from openqasm3.parser import QASM3ParsingError, parse

from .exceptions import QasmError


def extract_qasm_version(qasm: str) -> int:
    """
    Parses an OpenQASM program string to determine its version, either 2 or 3.

    Args:
        qasm (str): The OpenQASM program string.

    Returns:
        int: The OpenQASM version as an integer.

    Raises:
        QasmError: If the string does not represent a valid OpenQASM program.
    """
    qasm = qasm.replace("opaque", "// opaque")  # Temporarily mask out the opaque keyword
    try:
        parsed_program = parse(qasm)
        version = int(float(parsed_program.version))
        return version
    except (QASM3ParsingError, ValueError, TypeError) as err:
        raise QasmError("Could not determine the OpenQASM version.") from err


def get_qasm_type_alias(qasm: str) -> str:
    """
    Determines the type alias for an OpenQASM program based on its version.

    Args:
        qasm (str): The OpenQASM program string.

    Returns:
        str: The QASM version alias ('qasm2' or 'qasm3').

    Raises:
        QasmError: If the string does not represent a valid OpenQASM program.
    """
    try:
        version = extract_qasm_version(qasm)
        type_alias = f"qasm{version}"
        return type_alias
    except QasmError as err:
        raise QasmError(
            "Could not determine the type alias: the OpenQASM program may be invalid."
        ) from err


class BaseQasmInstanceMeta(type):
    """Metaclass for OpenQASM type checking based on string content.

    Attributes:
        version (Optional[int]): The specific OpenQASM type to check for.
    """

    version: Optional[int] = None

    def __instancecheck__(cls, instance):
        """Custom instance checks based on OpenQASM type.

        Args:
            instance: The object to check.

        Returns:
            bool: True if instance is a string matching the OpenQASM type, False otherwise.
        """
        if not isinstance(instance, str):
            return False
        try:
            return extract_qasm_version(instance) == cls.version
        except QasmError:
            return False


class Qasm2InstanceMeta(BaseQasmInstanceMeta):
    """Metaclass for instances representing OpenQASM 2 strings."""

    version = 2


class Qasm3InstanceMeta(BaseQasmInstanceMeta):
    """Metaclass for instances representing OpenQASM 3 strings."""

    version = 3


class Qasm2Instance(metaclass=Qasm2InstanceMeta):
    """Marker class for strings that are valid OpenQASM 2 programs."""


class Qasm3Instance(metaclass=Qasm3InstanceMeta):
    """Marker class for strings that are valid OpenQASM 3 programs."""


class QasmString(str):
    """Base class for OpenQASM string types, providing validation upon instantiation."""

    version: Optional[int] = None

    def __new__(cls, value):
        if not isinstance(value, str):
            raise TypeError("OpenQASM strings must be initialized with a string.")
        if not extract_qasm_version(value) == cls.version:
            raise ValueError(f"String does not conform to OpenQASM {cls.version} format.")
        return str.__new__(cls, value)


class Qasm2String(QasmString):
    """Specifically typed string for OpenQASM 2 formatted text."""

    version = 2


class Qasm3String(QasmString):
    """Specifically typed string for OpenQASM 3 formatted text."""

    version = 3

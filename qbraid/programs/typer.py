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
Module providing granular type checking for quantum programs
that use Python's built-in types.

"""
from typing import Any, Optional, TypeVar

from openqasm3.parser import QASM3ParsingError, parse

from .exceptions import QasmError

IonQDictType = TypeVar("IonQDictType", bound=dict)


class IonQDictInstanceMeta(type):
    """Metaclass for IonQ JSON type checking based on dict content."""

    def __instancecheck__(cls, instance):
        """Custom instance checks based on dict format."""
        if not isinstance(instance, dict):
            return False

        qubits = instance.get("qubits")
        circuit = instance.get("circuit")
        if not isinstance(qubits, int) or not isinstance(circuit, list):
            return False

        for op in circuit:
            if not isinstance(op, dict):
                return False

            gate = op.get("gate")
            rotation = op.get("rotation")
            target, targets = op.get("target"), op.get("targets")
            control, controls = op.get("control"), op.get("controls")

            if not isinstance(gate, str):
                return False

            if rotation is not None and not isinstance(rotation, (int, float)):
                return False

            if not cls._validate_targets(target, targets):
                return False

            if not cls._validate_controls(control, controls):
                return False

        return True

    @staticmethod
    def _validate_targets(target: Any, targets: Any) -> bool:
        """Helper method to validate target and targets."""
        if target is not None and targets is not None:
            return False
        if target is not None and not isinstance(target, int):
            return False
        if targets is not None:
            if not isinstance(targets, list) or not all(isinstance(t, int) for t in targets):
                return False
        return True

    @staticmethod
    def _validate_controls(control: Any, controls: Any) -> bool:
        """Helper method to validate control and controls."""
        if control is not None and controls is not None:
            return False
        if control is not None and not isinstance(control, int):
            return False
        if controls is not None:
            if not isinstance(controls, list) or not all(isinstance(c, int) for c in controls):
                return False
        return True


class IonQDict(metaclass=IonQDictInstanceMeta):
    """Marker class for dict that are valid IonQ JSON formatted programs."""


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

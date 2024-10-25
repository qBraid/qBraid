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
from abc import ABCMeta, abstractmethod
from typing import Any, Optional, Type, TypeVar

from openqasm3.parser import QASM3ParsingError, parse

from .exceptions import QasmError, ValidationError

IonQDictType = TypeVar("IonQDictType", bound=dict)


class QbraidMetaType(ABCMeta):
    """Abstract metaclass for custom program type checking based on built-in types."""

    @property
    @abstractmethod
    def __alias__(cls) -> Optional[str]:
        """The program type alias to associate with the class."""

    @property
    @abstractmethod
    def __bound__(cls) -> Type[Any]:
        """The built-in type the class is wrapping."""

    def __repr__(cls) -> str:
        return "~" + cls.__name__


class IonQDictInstanceMeta(QbraidMetaType):
    """Metaclass for IonQ JSON type checking based on dict content."""

    @property
    def __alias__(cls) -> str:
        return "ionq"

    @property
    def __bound__(cls) -> Type[dict]:
        return dict

    @staticmethod
    def _validate_field(single: Any, multiple: Any, field_name: str) -> None:
        """Helper method to validate single or multiple target/control fields."""
        if single is not None and multiple is not None:
            raise ValidationError(
                f"Both {field_name} and {field_name}s are set; only one should be provided."
            )
        if single is not None and not isinstance(single, int):
            raise ValidationError(f"Invalid {field_name}: {single}. Must be an integer.")
        if multiple is not None and not (
            isinstance(multiple, list) and all(isinstance(item, int) for item in multiple)
        ):
            raise ValidationError(f"Invalid {field_name}s: {multiple}. Must be a list of integers.")

    def __instancecheck__(cls, instance: Any) -> bool:
        """Custom instance checks based on dict format."""
        if not isinstance(instance, dict):
            return False

        qubits = instance.get("qubits")
        circuit = instance.get("circuit")
        gateset = instance.get("gateset")

        if gateset is not None and not isinstance(gateset, str):
            return False

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

            try:
                cls._validate_field(target, targets, "target")
                cls._validate_field(control, controls, "control")
            except ValidationError:
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


class BaseQasmInstanceMeta(QbraidMetaType):
    """Metaclass for OpenQASM type checking based on string content.

    Attributes:
        version (Optional[int]): The specific OpenQASM type to check for.
    """

    version: Optional[int] = None

    @property
    def __alias__(cls) -> Optional[str]:
        if isinstance(cls.version, int):
            return f"qasm{cls.version}"
        return None

    @property
    def __bound__(cls) -> Type[str]:
        return str

    def __instancecheck__(cls, instance: Any) -> bool:
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


class Qasm2StringMeta(BaseQasmInstanceMeta):
    """Metaclass for instances representing OpenQASM 2 strings."""

    version = 2


class Qasm3StringMeta(BaseQasmInstanceMeta):
    """Metaclass for instances representing OpenQASM 3 strings."""

    version = 3


class Qasm2String(metaclass=Qasm2StringMeta):
    """Marker class for strings that are valid OpenQASM 2 programs."""


class Qasm3String(metaclass=Qasm3StringMeta):
    """Marker class for strings that are valid OpenQASM 3 programs."""


class QasmStringType(str):
    """Base class for OpenQASM string types, providing validation upon instantiation."""

    version: Optional[int] = None

    def __new__(cls, value):
        if not isinstance(value, str):
            raise TypeError("OpenQASM strings must be initialized with a string.")
        if not extract_qasm_version(value) == cls.version:
            raise ValueError(f"String does not conform to OpenQASM {cls.version} format.")
        return str.__new__(cls, value)


class Qasm2StringType(QasmStringType):
    """Specifically typed string for OpenQASM 2 formatted text."""

    version = 2


class Qasm3StringType(QasmStringType):
    """Specifically typed string for OpenQASM 3 formatted text."""

    version = 3

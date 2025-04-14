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

from pyqasm.analyzer import Qasm3Analyzer
from pyqasm.exceptions import QasmParsingError

from .exceptions import QasmError
from .exceptions import ValidationError as ProgramValidationError

IonQDictType = TypeVar("IonQDictType", bound=dict)
QuboCoefficientsDictType = TypeVar("QuboCoefficientsDictType", bound=dict)


class QbraidMetaType(ABCMeta):
    """Abstract metaclass for custom program type checking based on built-in types."""

    @property
    @abstractmethod
    def __alias__(cls) -> str | None:
        """The program type alias to associate with the class."""

    @property
    @abstractmethod
    def __bound__(cls) -> Type[Any]:
        """The built-in type the class is wrapping."""


class QuboCoefficientsDictInstanceMeta(QbraidMetaType):
    """Metaclass for Qubo coefficients JSON type checking based on dict content."""

    @property
    def __alias__(cls) -> str:
        return "qubo"

    @property
    def __bound__(cls) -> Type[dict]:
        return dict

    def __instancecheck__(cls, instance: Any) -> bool:
        """Custom instance checks based on dict format."""
        if not instance or not isinstance(instance, dict):
            return False

        for key, value in instance.items():
            if not (
                isinstance(key, tuple) and len(key) == 2 and all(isinstance(k, str) for k in key)
            ):
                return False

            if not isinstance(value, (float, int)):
                return False

        return True


class QuboCoefficientsDict(metaclass=QuboCoefficientsDictInstanceMeta):
    """Marker class for dict that are valid Qubo coefficients format."""


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
            raise ProgramValidationError(
                f"Both {field_name} and {field_name}s are set; only one should be provided."
            )
        if single is not None and not isinstance(single, int):
            raise ProgramValidationError(f"Invalid {field_name}: {single}. Must be an integer.")
        if multiple is not None and not (
            isinstance(multiple, list) and all(isinstance(item, int) for item in multiple)
        ):
            raise ProgramValidationError(
                f"Invalid {field_name}s: {multiple}. Must be a list of integers."
            )

    def __instancecheck__(cls, instance: Any) -> bool:
        """Custom instance checks based on dict format."""
        if not isinstance(instance, dict):
            return False

        qubits = instance.get("qubits")
        circuit = instance.get("circuit")
        gateset = instance.get("gateset")
        ciruit_format = instance.get("format")

        if ciruit_format is not None and not isinstance(ciruit_format, str):
            return False

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
            except ProgramValidationError:
                return False

        return True


class IonQDict(metaclass=IonQDictInstanceMeta):
    """Marker class for dict that are valid IonQ JSON formatted programs."""


class BaseQasmInstanceMeta(QbraidMetaType):
    """Metaclass for OpenQASM type checking based on string content.

    Attributes:
        version (int | str | None): The specific OpenQASM type to check for.
    """

    version: int | str | None = None
    extension: str | None = None

    @property
    def __alias__(cls) -> str | None:
        if isinstance(cls.version, int):
            return f"qasm{cls.version}{'_' + cls.extension if cls.extension else ''}"
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
            return int(Qasm3Analyzer.extract_qasm_version(instance)) == cls.version
        except QasmParsingError:
            return False


class Qasm2StringMeta(BaseQasmInstanceMeta):
    """Metaclass for instances representing OpenQASM 2 strings."""

    version = 2


class Qasm3StringMeta(BaseQasmInstanceMeta):
    """Metaclass for instances representing OpenQASM 3 strings."""

    version = 3


class Qasm2KirinStringMeta(BaseQasmInstanceMeta):
    """Metaclass for instances representing OpenQASM 2 strings adapted for Kirin parser."""

    version = 2
    extension = "kirin"

    def __instancecheck__(cls, instance: Any) -> bool:
        """Custom instance checks for Kirin OpenQASM 2 type.

        Args:
            instance: The object to check.

        Returns:
            bool: True if instance is a string matching the
                Kirin OpenQASM 2 type, False otherwise.
        """
        return isinstance(instance, str) and instance.lstrip().startswith("KIRIN")


class Qasm2String(metaclass=Qasm2StringMeta):
    """Marker class for strings that are valid OpenQASM 2 programs."""


class Qasm3String(metaclass=Qasm3StringMeta):
    """Marker class for strings that are valid OpenQASM 3 programs."""


class Qasm2KirinString(metaclass=Qasm2KirinStringMeta):
    """Marker class for strings that are valid OpenQASM 2 programs."""


class QasmStringType(str):
    """Base class for OpenQASM string types, providing validation upon instantiation."""

    version: Optional[int] = None

    def __new__(cls, value):
        if not isinstance(value, str):
            raise TypeError("OpenQASM strings must be initialized with a string.")
        if not int(Qasm3Analyzer.extract_qasm_version(value)) == cls.version:
            raise ValueError(f"String does not conform to OpenQASM {cls.version} format.")
        return str.__new__(cls, value)


class Qasm2StringType(QasmStringType):
    """Specifically typed string for OpenQASM 2 formatted text."""

    version = 2


class Qasm3StringType(QasmStringType):
    """Specifically typed string for OpenQASM 3 formatted text."""

    version = 3


def get_qasm_type_alias(qasm: str) -> str:
    """
    Determines the type alias for an OpenQASM program based on its version.

    Args:
        qasm (str): The OpenQASM program string.

    Returns:
        str: The QASM version alias ('qasm2', 'qasm3', or 'qasm2_kirin').

    Raises:
        QasmError: If the string does not represent a valid OpenQASM program.
    """
    if isinstance(qasm, Qasm2String):
        return Qasm2String.__alias__
    if isinstance(qasm, Qasm3String):
        return Qasm3String.__alias__
    if isinstance(qasm, Qasm2KirinString):
        return Qasm2KirinString.__alias__
    raise QasmError("Could not determine the type alias: the OpenQASM program may be invalid.")


QBRAID_META_TYPES = {IonQDict, QuboCoefficientsDict}
BOUND_QBRAID_META_TYPES = {Qasm2String, Qasm3String, Qasm2KirinString}

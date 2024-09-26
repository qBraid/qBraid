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
Module defining qBraid runtime base schema,
with a shared header for semantic versioning.

"""
from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, Union

import qbraid_core.decimal
from pydantic import BaseModel, Field, GetCoreSchemaHandler, computed_field, model_validator
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing_extensions import Annotated, Self


class QbraidSchemaHeader(BaseModel):
    """Represents the header for a qBraid schema.

    Attributes:
        name (str): Name of the schema, typically the package and module.
        version (float): Version number of the schema.
    """

    name: Annotated[str, Field(strict=True, min_length=1)]
    version: Annotated[float, Field(strict=True, gt=0)]


class QbraidSchemaBase(BaseModel):
    """Base class for qBraid schemas that require a valid version in subclasses.

    Attributes:
        header (QbraidSchemaHeader): The schema header.
    """

    VERSION: ClassVar[float]  # Must be defined in subclasses

    @computed_field(alias="schemaHeader")
    @property
    def header(self) -> QbraidSchemaHeader:
        """Computes the schema header based on the module name and class version.

        Returns:
            QbraidSchemaHeader: The computed schema header.

        Raises:
            ValueError: If 'VERSION' is not defined or invalid.
        """
        if (
            not hasattr(self.__class__, "VERSION")
            or not isinstance(self.__class__.VERSION, (int, float))
            or self.__class__.VERSION <= 0
        ):
            raise ValueError(
                f"{self.__class__.__name__} must define a valid semantic version for 'VERSION'."
            )

        module_name = self.__class__.__module__
        return QbraidSchemaHeader(name=module_name, version=float(self.__class__.VERSION))

    @model_validator(mode="after")
    def validate_header(self) -> Self:
        """Validates that the header is correctly set up during instantiation."""
        try:
            self.header
        except ValueError as err:
            raise err
        return self


class Credits(qbraid_core.decimal.Credits):
    """Represents a value in Credits, subclassing decimal.Decimal.

    Args:
        value (str or int or float): The initial value for the Credits.
    """

    @classmethod
    def __get_pydantic_core_schema__(  # pylint: disable-next=unused-argument
        cls, source_type: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Provide Pydantic with a schema for the Credits type."""
        number_schema = core_schema.union_schema(
            [
                core_schema.int_schema(),
                core_schema.float_schema(),
                handler(Decimal),
            ],
            strict=False,
            custom_error_type="credits_type",
            custom_error_message="Input should be a number (int, float, or Decimal)",
        )

        # pylint: disable-next=unused-argument
        def to_credits(value: Union[int, float, Decimal], info) -> "Credits":
            return cls(value)

        return core_schema.with_info_after_validator_function(to_credits, number_schema)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler
    ) -> JsonSchemaValue:
        """Provide a JSON schema for the Credits type."""
        json_schema = handler(core_schema)
        json_schema.update(
            title="Credits",
            description="A monetary amount where 1 Credit = $0.01 USD.",
            examples=[10, 0.05, 1.5],
            type="number",
        )
        return json_schema


class USD(qbraid_core.decimal.USD):
    """Represents a value in U.S. Dollars, subclassing decimal.Decimal.

    Args:
        value (str or int or float): The initial value for the USD.
    """

    @classmethod
    def __get_pydantic_core_schema__(  # pylint: disable-next=unused-argument
        cls, source_type: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Provide Pydantic with a schema for the USD type."""
        number_schema = core_schema.union_schema(
            [
                core_schema.int_schema(),
                core_schema.float_schema(),
                handler(Decimal),
            ],
            strict=False,
            custom_error_type="usd_type",
            custom_error_message="Input should be a number (int, float, or Decimal)",
        )

        # pylint: disable-next=unused-argument
        def to_usd(value: Union[int, float, Decimal], info) -> "USD":
            return cls(value)

        return core_schema.with_info_after_validator_function(to_usd, number_schema)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler
    ) -> JsonSchemaValue:
        """Provide a JSON schema for the USD type."""
        json_schema = handler(core_schema)
        json_schema.update(
            title="USD",
            description="A monetary amount representing U.S. Dollars.",
            examples=[10, 0.05, 1.5],
            type="number",
        )
        return json_schema

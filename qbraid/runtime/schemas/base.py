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
Module defining qBraid runtime base schema,
with a shared header for semantic versioning.

"""
from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field, computed_field, model_validator
from qbraid_core.decimal import USD, Credits
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

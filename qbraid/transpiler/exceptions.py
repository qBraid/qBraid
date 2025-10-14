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
Module defining exceptions for errors raised during conversions

"""
from typing import Optional

from qbraid.exceptions import QbraidError


class ProgramConversionError(QbraidError):
    """Base class for errors raised while converting a circuit."""


class NodeNotFoundError(ValueError, QbraidError):
    """Class for errors raised when a node is not present in a ConversionGraph."""

    def __init__(self, graph_type: str, package: str, nodes: list[str]):
        message = (
            f"{graph_type} conversion graph does not contain node '{package}'. "
            f"Supported nodes are: {nodes}"
        )
        super().__init__(message)


class ConversionPathNotFoundError(QbraidError):
    """Class for errors raised when there is no path between two nodes in a ConversionGraph."""

    def __init__(self, source: str, target: str, max_depth: Optional[int] = None):
        max_depth_msg = f" with depth <= {max_depth}" if max_depth is not None else ""
        message = f"No conversion path found from '{source}' to '{target}'{max_depth_msg}"
        super().__init__(message)

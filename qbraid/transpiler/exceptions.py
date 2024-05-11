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
Module defining exceptions for errors raised during conversions

"""
from typing import Optional

from qbraid.exceptions import QbraidError


class CircuitConversionError(QbraidError):
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

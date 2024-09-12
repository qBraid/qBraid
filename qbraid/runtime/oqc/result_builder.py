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
Module for OQC result class.

"""
from typing import Any

from qbraid.runtime.result import GateModelResultBuilder


class OQCGateModelResultBuilder(GateModelResultBuilder):
    """OQC result class."""

    def __init__(self, result: dict[str, Any]):
        self._result = result

    def get_counts(self) -> dict[str, int]:
        """Get the raw measurement counts of the task."""
        result: dict[str, Any] = self._result
        return result.get("counts", {})

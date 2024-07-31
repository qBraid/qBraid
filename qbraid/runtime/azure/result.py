# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
#
# pylint: disable=arguments-differ


"""
Module defining Azure Results class

"""
from typing import Any

import numpy as np

from qbraid.runtime.result import GateModelJobResult


class AzureQuantumResult(GateModelJobResult):
    """Azure result class."""

    def __init__(self, result: dict[str, Any]):
        super().__init__(result)
        self._counts = None
        self._measurements = None

    def measurements(self) -> np.ndarray:
        """Return the measurements as a 2D numpy array."""
        if self._measurements is None:
            counts = self.raw_counts()
            if counts:
                measurements = []
                for state, count in counts.items():
                    measurements.extend([list(map(int, state))] * count)
                self._measurements = np.array(measurements, dtype=int)
        return self._measurements

    def raw_counts(self, **kwargs) -> dict[str, int]:
        """Return the raw counts from the result data."""
        return self._result["results"][0]["data"]["counts"]

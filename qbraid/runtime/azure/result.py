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

from collections import Counter

import numpy as np

from qbraid.runtime.result import GateModelJobResult


class AzureResult(GateModelJobResult):
    """Azure result class."""

    def __init__(self, result: dict):
        super().__init__(result=result)
        self._result = result

    def measurements(self):
        """Return the measurements from the result data."""
        return np.array(self._result["meas"])

    def measurement_counts(self):
        return dict(Counter(self.measurements()))

    def raw_counts(self, **kwargs):
        """Return the raw counts from the result data."""
        return self._result.values()

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
# pylint: disable=invalid-overridden-method

"""
Module defining Azure Results class

"""

from qbraid.runtime.result import GateModelJobResult


class AzureResult(GateModelJobResult):
    """Azure result class."""

    def __init__(self, result_data: dict):
        self._data = result_data

    @property
    def data(self) -> dict:
        """Return the Azure Result data."""
        return self._data

    @property
    def measurements(self):
        """Return the measurements from the result data."""
        # Implement this method based on the structure of your result data
        return self._data.keys()

    # pylint:disable=arguments-differ
    @property
    def raw_counts(self):
        """Return the raw counts from the result data."""
        # Implement this method based on the structure of your result data
        return self._data.values()

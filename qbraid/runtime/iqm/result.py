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

from qbraid.runtime.result import GateModelJobResult

class IQMJobResult(GateModelJobResult):
    """OQC result class."""

    def raw_counts(self, **kwargs):
        """Get the raw measurement counts of the task."""
        raise NotImplementedError

    def measurements(self):
        """Get the measurements of the task."""
        raise NotImplementedError
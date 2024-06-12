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
import numpy as np

from qbraid.runtime.result import GateModelJobResult


class OQCJobResult(GateModelJobResult):
    """OQC result class."""

    def raw_counts(self, **kwargs) -> dict[str, int]:
        """Get the raw measurement counts of the task."""
        return self._result.get("counts", {})

    def measurements(self) -> np.ndarray:
        """Get the measurements of the task."""
        counts = self.raw_counts()
        res = []
        for state in counts:
            new_state = []
            for bit in state:
                new_state.append(int(bit))
            for _ in range(counts[state]):
                res.append(new_state)
        return np.array(res, dtype=int)

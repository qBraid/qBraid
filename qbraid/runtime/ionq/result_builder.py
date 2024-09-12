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
Module defining IonQ result class

"""
from typing import Any, Optional

from qbraid.runtime.result import GateModelResultBuilder


class IonQGateModelResultBuilder(GateModelResultBuilder):
    """IonQ result class."""

    def __init__(self, result: dict[str, Any]):
        self._result = result
        self._counts = None

    def get_counts(self) -> dict[str, int]:
        """Return the raw counts of the run."""
        if self._counts is None:
            result: dict[str, Any] = self._result
            shots: Optional[int] = result.get("shots")
            probs_int: Optional[dict] = result.get("probabilities")
            if shots and probs_int:
                probs_binary = {
                    bin(int(key))[2:].zfill(2): value for key, value in probs_int.items()
                }
                probs_normal = self.normalize_bit_lengths(probs_binary)
                self._counts = {state: int(prob * shots) for state, prob in probs_normal.items()}
        return self._counts

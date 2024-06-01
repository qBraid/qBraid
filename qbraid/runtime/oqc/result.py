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
from typing import TYPE_CHECKING

import numpy as np

from qbraid.runtime.result import QuantumJobResult

if TYPE_CHECKING:
    import qcaas_client.client


class OQCJobResult(QuantumJobResult):
    """OQC result class."""

    def __init__(self, job_id: str, qpu_id: str, client: "qcaas_client.client.OQCClient"):
        super().__init__()
        self.id = job_id
        self._qpu_id = qpu_id
        self._client = client

    def raw_counts(self, **kwargs) -> dict[str, int]:
        return self._client.get_task_results(
            task_id=self.id, qpu_id=self._qpu_id, **kwargs
        ).result.get("c")

    def measurements(self) -> np.ndarray:
        counts = self.raw_counts()
        res = []
        for state in counts:
            new_state = []
            for bit in state:
                new_state.append(int(bit))
            for _ in range(counts[state]):
                res.append(new_state)
        return np.array(res, dtype=int)

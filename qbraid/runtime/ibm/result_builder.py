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
Module defining QiskitGateModelResultBuilder Class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np
from qiskit.exceptions import QiskitError
from qiskit.primitives.containers import PrimitiveResult

from qbraid._logging import logger
from qbraid.runtime.postprocess import normalize_tuples

if TYPE_CHECKING:
    from qiskit.result import Result
    from qiskit_ibm_runtime.utils.runner_result import RunnerResult


class QiskitGateModelResultBuilder:
    """Qiskit ``Result`` wrapper class."""

    def __init__(self, result: PrimitiveResult | RunnerResult | Result):
        self._result = result

    def _format_measurements(self, memory_list: list[str]) -> list[list[int]]:
        """Format the measurements into int for the given memory list"""
        formatted_meas = []
        for str_shot in memory_list:
            lst_shot = [int(x) for x in list(str_shot)]
            formatted_meas.append(lst_shot)
        return formatted_meas

    def measurements(self) -> Optional[np.ndarray | list[np.ndarray]]:
        """Return measurements a 2D numpy array"""
        if isinstance(self._result, PrimitiveResult):
            meas = [pub_result.join_data().array for pub_result in self._result]
            return meas[0] if len(meas) == 1 else meas

        num_circuits = len(self._result.results)

        try:
            qiskit_meas = [self._result.get_memory(i) for i in range(num_circuits)]
        except QiskitError as err:
            logger.warning("Memory states (measurements) data not available for this job: %s", err)
            return None

        qbraid_meas = [self._format_measurements(qiskit_meas[i]) for i in range(num_circuits)]

        if num_circuits == 1:
            qbraid_meas = qbraid_meas[0]
        else:
            qbraid_meas = normalize_tuples(qbraid_meas)

        return np.array(qbraid_meas)

    def get_counts(self) -> dict[str, int] | list[dict[str, int]]:
        """Returns the histogram data of the run"""
        if isinstance(self._result, PrimitiveResult):
            counts = [pub_result.join_data().get_counts() for pub_result in self._result]
            return counts[0] if len(counts) == 1 else counts
        return self._result.get_counts()

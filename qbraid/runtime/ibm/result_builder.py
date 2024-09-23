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
Module defining QiskitGateModelResultBuilder Class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

import numpy as np
from qiskit.exceptions import QiskitError

from qbraid._logging import logger
from qbraid.runtime.postprocess import normalize_tuples

if TYPE_CHECKING:
    from qiskit.result import Result
    from qiskit_ibm_runtime.utils.runner_result import RunnerResult


class QiskitGateModelResultBuilder:
    """Qiskit ``Result`` wrapper class."""

    def __init__(self, result: Union[RunnerResult, Result]):
        self._result = result

    def _format_measurements(self, memory_list: list[str]) -> list[list[int]]:
        """Format the measurements into int for the given memory list"""
        formatted_meas = []
        for str_shot in memory_list:
            lst_shot = [int(x) for x in list(str_shot)]
            formatted_meas.append(lst_shot)
        return formatted_meas

    def measurements(self) -> Optional[Union[np.ndarray, list[np.ndarray]]]:
        """Return measurements a 2D numpy array"""
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

    def get_counts(self) -> Union[dict[str, int], list[dict[str, int]]]:
        """Returns the histogram data of the run"""
        return self._result.get_counts()

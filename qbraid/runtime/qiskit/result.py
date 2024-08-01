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
Module defining QiskitResult Class

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from qbraid.runtime.result import GateModelJobResult

if TYPE_CHECKING:
    from qiskit.result import Result


class QiskitResult(GateModelJobResult):
    """Qiskit ``Result`` wrapper class."""

    @staticmethod
    def normalize_tuples(measurements: list[list[tuple[int, ...]]]) -> list[list[tuple[int, ...]]]:
        """
        Normalizes lists of tuples in a list to have the same tuple length across all entries
        by padding shorter tuples with zeros on the left.

        Args:
            measurements (list[list[tuple[int, ...]]]): A list of lists containing tuples
                with integer elements.

        Returns:
            list[list[tuple[int, ...]]]: A new list where each sublist's tuples have normalized
                lengths, preserving the binary significance of the numbers.
        """
        max_tuple_length = max(len(tup) for sublist in measurements for tup in sublist)

        normalized_measurements = []
        for sublist in measurements:
            normalized_sublist = []
            for tup in sublist:
                current_tuple = tuple(tup) if isinstance(tup, list) else tup
                padded_tuple = (0,) * (max_tuple_length - len(current_tuple)) + current_tuple
                normalized_sublist.append(padded_tuple)
            normalized_measurements.append(normalized_sublist)

        return normalized_measurements

    def _format_measurements(self, memory_list):
        """Format the measurements into int for the given memory list"""
        formatted_meas = []
        for str_shot in memory_list:
            lst_shot = [int(x) for x in list(str_shot)]
            formatted_meas.append(lst_shot)
        return formatted_meas

    def measurements(self) -> np.ndarray:
        """Return measurements a 2D numpy array"""
        result: Result = self._result
        num_circuits = len(result.results)
        qiskit_meas = [result.get_memory(i) for i in range(num_circuits)]
        qbraid_meas = [self._format_measurements(qiskit_meas[i]) for i in range(num_circuits)]

        if num_circuits == 1:
            qbraid_meas = qbraid_meas[0]
        else:
            qbraid_meas = self.normalize_tuples(qbraid_meas)

        return np.array(qbraid_meas)

    def get_counts(self) -> dict[str, int]:
        """Returns the histogram data of the run"""
        result: Result = self._result
        return result.get_counts()

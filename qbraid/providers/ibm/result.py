# Copyright (C) 2023 qBraid
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
import numpy as np

from qbraid.providers.result import QuantumJobResult


class QiskitResult(QuantumJobResult):
    """Qiskit ``Result`` wrapper class."""

    def _format_measurements(self, memory_list):
        """Format the measurements into int for the given memory list"""
        formatted_meas = []
        for str_shot in memory_list:
            lst_shot = [int(x) for x in list(str_shot)]
            formatted_meas.append(lst_shot)
        return formatted_meas

    def measurements(self):
        """Return measurements as list"""
        num_circuits = len(self._result.results)
        qiskit_meas = [self._result.get_memory(i) for i in range(num_circuits)]
        qbraid_meas = [self._format_measurements(qiskit_meas[i]) for i in range(num_circuits)]

        if num_circuits == 1:
            qbraid_meas = qbraid_meas[0]

        return np.array(qbraid_meas)

    def raw_counts(self):
        """Returns the histogram data of the run"""
        return self._result.get_counts()

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
Module defining IBMResultWrapper Class

"""
import numpy as np

from qbraid.devices.result import ResultWrapper


class IBMResultWrapper(ResultWrapper):
    """Qiskit ``Result`` wrapper class."""

    def measurements(self):
        """Return measurements as list"""
        qiskit_meas = self.vendor_rlo.get_memory()
        qbraid_meas = []
        for str_shot in qiskit_meas:
            lst_shot = [int(x) for x in list(str_shot)]
            qbraid_meas.append(lst_shot)
        return np.array(qbraid_meas)

    def raw_counts(self):
        """Returns the histogram data of the run"""
        return self.vendor_rlo.get_counts()

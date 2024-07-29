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
Device class for IQM devices.

"""
from iqm.qiskit_iqm import transpile_to_IQM
from qiskit import execute

from qbraid.runtime.device import QuantumDevice

from .job import IQMJob


class IQMDevice(QuantumDevice):
    """Device class for IQM devices."""

    def __init__(self, profile, backend):
        """Create an IQMDevice object."""
        super().__init__(profile)
        self.backend = backend

    def status(self):
        """Return the status of the device."""
        raise NotImplementedError

    def submit(self, run_input):
        """Submit a run to the device."""
        qjob = transpile_to_IQM(run_input)
        job = execute(qjob, backend=self.backend)
        return IQMJob(job_id=job.job_id(), job=job)

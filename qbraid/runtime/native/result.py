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
Module defining :py:class:`ResultData` subclasses for runtime jobs that are
managed natively through qBraid.

"""
from __future__ import annotations

from typing import Optional

from qbraid.runtime.result_data import AnnealingResultData, GateModelResultData


class QbraidQirSimulatorResultData(GateModelResultData):
    """Class for storing and accessing the results of a qBraid QIR simulator job."""

    def __init__(self, backend_version: str, seed: Optional[int] = None, **kwargs):
        """Create a new QbraidQirSimulatorResultData instance."""
        super().__init__(**kwargs)
        self._backend_version = backend_version
        self._seed = seed

    @property
    def backend_version(self) -> str:
        """Returns the version of the simulator backend used."""
        return self._backend_version

    @property
    def seed(self) -> Optional[int]:
        """Returns the seed used for the simulation."""
        return self._seed


class Equal1SimulatorResultData(GateModelResultData):
    """Class for storing and accessing the results of an Equal1 simulator job."""


class NECVectorAnnealerResultData(AnnealingResultData):
    """Class for storing and accessing the results of an NEC job."""

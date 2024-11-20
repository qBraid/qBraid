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

from typing import TYPE_CHECKING, Any, Optional

import flair_visual.simulation_result

from qbraid.runtime.result import AnnealingResultData, GateModelResultData
from flair_visual.simulation_result import QuEraSimulationResult

if TYPE_CHECKING:
    import flair_visual.animation.runtime.qpustate
    import pandas as pd


class QuEraQasmSimulatorResultData(GateModelResultData):
    """Class for storing and accessing the results of a QuEra QASM simulator job."""

    def __init__(self, backend: str, quera_simulation_result: dict[str, Any], **kwargs):
        """Create a new QuEraSimulatorResultData instance."""
        super().__init__(**kwargs)
        self._backend = backend
        if quera_simulation_result == {}:    
            self._quera_simulation_result = QuEraSimulationResult.from_json(quera_simulation_result)
        else:
            self._quera_simulation_result = None

    @property
    def backend(self) -> str:
        """Returns the backend used."""
        return self._backend

    @property
    def quera_simulation_result(self) -> QuEraSimulationResult:
        """Returns the QuEra simulation result."""
        if self._quera_simulation_result is None:
            raise ValueError("The simulation result is not available.")
        
        return self._quera_simulation_result

    @property
    def flair_visual_version(self) -> Optional[str]:
        """Returns the version of the flair visualizer used."""
        
        return self.quera_simulation_result.flair_visual_version

    def get_qpu_state(self) -> flair_visual.animation.runtime.qpustate.AnimateQPUState:
        """Returns the the state of the QPU atoms used in the simulation."""

        return self.quera_simulation_result.atom_animation_state

    def get_logs(self) -> pd.DataFrame:
        """Returns the logs generated during the simulation as a pandas DataFrame."""
        
        return self.quera_simulation_result.logs


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


class NECVectorAnnealerResultData(AnnealingResultData):
    """Class for storing and accessing the results of an NEC job."""

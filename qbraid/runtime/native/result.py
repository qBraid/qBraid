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
Module defining :py:class:`ResultData` subclasses for runtime jobs that are
managed natively through qBraid.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from qbraid.exceptions import QbraidError
from qbraid.runtime.result_data import AnnealingResultData, GateModelResultData

if TYPE_CHECKING:
    import flair_visual.animation.runtime.qpustate
    import flair_visual.simulation_result
    import pandas as pd


class QuEraQasmSimulatorResultData(GateModelResultData):
    """Class for storing and accessing the results of a QuEra QASM simulator job."""

    def __init__(
        self, backend: str, quera_simulation_result: Optional[dict[str, Any]] = None, **kwargs
    ):
        """Create a new QuEraSimulatorResultData instance."""
        super().__init__(**kwargs)
        self._backend = backend
        self._quera_simulation_result: Optional[
            flair_visual.simulation_result.QuEraSimulationResult
        ] = (
            self._initialize_simulation_result(quera_simulation_result)
            if quera_simulation_result
            else None
        )

    @property
    def backend(self) -> str:
        """Returns the backend used."""
        return self._backend

    def _initialize_simulation_result(
        self, value: dict[str, Any]
    ) -> flair_visual.simulation_result.QuEraSimulationResult:
        """Initialize the QuEra simulation result during construction."""
        try:
            # pylint: disable-next=import-outside-toplevel
            from flair_visual.simulation_result import QuEraSimulationResult

            return QuEraSimulationResult.from_json(value)
        except ImportError as err:  # pragma: no cover
            raise QbraidError(
                "Missing required package 'flair-visual'. "
                "Install with 'pip install flair-visual' or 'pip install qbraid[quera]'."
            ) from err

    @property
    def quera_simulation_result(self) -> flair_visual.simulation_result.QuEraSimulationResult:
        """Returns the QuEra simulation result."""
        if self._quera_simulation_result is None:
            raise ValueError("The simulation result is not available.")
        return self._quera_simulation_result

    @property
    def flair_visual_version(self) -> str:
        """Returns the version of the flair visualizer used."""
        return self.quera_simulation_result.flair_visual_version

    def get_qpu_state(self) -> flair_visual.animation.runtime.qpustate.AnimateQPUState:
        """Returns the state of the QPU atoms used in the simulation."""
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


class Equal1SimulatorResultData(GateModelResultData):
    """Class for storing and accessing the results of an Equal1 simulator job."""


class NECVectorAnnealerResultData(AnnealingResultData):
    """Class for storing and accessing the results of an NEC job."""

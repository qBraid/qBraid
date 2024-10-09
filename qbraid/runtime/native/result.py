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

from qbraid.runtime.result import AnnealingResultData, GateModelResultData

if TYPE_CHECKING:
    import flair_visual.animation.runtime.qpustate
    import pandas as pd


class QuEraQasmSimulatorResultData(GateModelResultData):
    """Class for storing and accessing the results of a QuEra QASM simulator job."""

    def __init__(
        self,
        backend: str,
        flair_visual_version: Optional[str] = None,
        atom_animation_state: Optional[dict[str, Any]] = None,
        logs: Optional[list[dict[str, Any]]] = None,
        **kwargs,
    ):
        """Create a new QuEraSimulatorResultData instance."""
        super().__init__(**kwargs)
        self._backend = backend
        self._flair_visual_version = flair_visual_version
        self._atom_animation_state = atom_animation_state
        self._logs = logs if logs else []

    @property
    def backend(self) -> str:
        """Returns the backend used."""
        return self._backend

    @property
    def flair_visual_version(self) -> Optional[str]:
        """Returns the version of the flair visualizer used."""
        return self._flair_visual_version

    def get_qpu_state(self) -> flair_visual.animation.runtime.qpustate.AnimateQPUState:
        """Returns the the state of the QPU atoms used in the simulation."""
        # pylint: disable-next=import-outside-toplevel
        from flair_visual.animation.runtime.qpustate import AnimateQPUState

        if self._atom_animation_state is None:
            raise ValueError("No atom_animation_state found in the result data.")

        return AnimateQPUState.from_json(self._atom_animation_state)

    def get_logs(self) -> pd.DataFrame:
        """Returns the logs generated during the simulation as a pandas DataFrame."""
        # pylint: disable-next=import-outside-toplevel
        from pandas import DataFrame

        return DataFrame(self._logs)


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

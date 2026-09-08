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

"""Client wrapper for resource estimates returned by the qBraid runtime API."""

from __future__ import annotations

from time import sleep, time
from typing import TYPE_CHECKING

from qbraid_core.exceptions import RequestsApiError
from qbraid_core.services.runtime import QuantumRuntimeClient, QuantumRuntimeServiceRequestError
from qbraid_core.services.runtime.schemas.estimate import (
    CircuitFeatures,
    Estimate,
    EstimateStatus,
    FrontierPoint,
    Infeasible,
)

from qbraid.runtime.exceptions import QbraidRuntimeError

if TYPE_CHECKING:
    import pandas as pd


class QbraidEstimate:
    """A resource estimate and the client used to refresh it.

    Args:
        estimate: The runtime API's estimate model.
        client: The authenticated runtime client that created the estimate.
    """

    def __init__(self, estimate: Estimate, client: QuantumRuntimeClient) -> None:
        self._estimate = estimate
        self._client = client

    @property
    def id(self) -> str:
        """Return the estimate identifier."""
        return self._estimate.id

    @property
    def status(self) -> EstimateStatus:
        """Return the last retrieved status; use :meth:`refresh` to update it."""
        return self._estimate.status

    def refresh(self) -> QbraidEstimate:
        """Retrieve the current estimate from the runtime API and return self."""
        try:
            response = self._client.session.get(f"/estimates/{self.id}")
            self._estimate = Estimate.model_validate(response.json()["data"])
        except RequestsApiError as err:
            raise QuantumRuntimeServiceRequestError(
                f"Failed to retrieve estimate '{self.id}': {err}"
            ) from err
        return self

    def wait(self, timeout: int = 300, poll: float = 2.0) -> QbraidEstimate:
        """Poll until the estimate completes and return self.

        Args:
            timeout: Maximum seconds to wait. Defaults to 300 seconds.
            poll: Seconds between queries. Defaults to 2 seconds.

        Raises:
            TimeoutError: If the estimate does not finish before the timeout.
            QbraidRuntimeError: If estimation fails, including the API's error.
        """
        start_time = time()
        terminal_states = {EstimateStatus.COMPLETED, EstimateStatus.FAILED}
        while self.status not in terminal_states:
            self.refresh()
            if self.status in terminal_states:
                break
            if time() - start_time >= timeout:
                raise TimeoutError(f"Timeout while waiting for estimate {self.id}.")
            sleep(poll)
        if self.status == EstimateStatus.FAILED:
            raise QbraidRuntimeError(f"Estimate {self.id} failed: {self._estimate.error}")
        return self

    @property
    def frontier(self) -> list[FrontierPoint]:
        """Return the feasible cost/quality frontier points with their bases."""
        return self._estimate.frontier

    @property
    def infeasible(self) -> list[Infeasible]:
        """Return excluded devices and their feasibility failure reasons."""
        return self._estimate.infeasible

    @property
    def open_questions(self) -> list[str]:
        """Return questions the estimator could not answer."""
        return self._estimate.openQuestions

    @property
    def narrative(self) -> str | None:
        """Return the generated explanation, if available."""
        return self._estimate.narrative

    @property
    def features(self) -> CircuitFeatures | None:
        """Return circuit features used for estimation, if available."""
        return self._estimate.features

    def to_dataframe(self) -> pd.DataFrame:
        """Return one row per frontier point, with scalar values and weakest basis.

        Basis is summarized across shots, minutes, all cost components, and quality.
        From weakest to strongest: ``unavailable``, ``assumed-default``,
        ``historical-regression``, ``computed``. Full quantities and intervals
        remain available through :attr:`frontier`.

        Raises:
            ImportError: If pandas is not installed.
        """
        try:
            import pandas as pd  # pylint: disable=import-outside-toplevel
        except ImportError as err:
            raise ImportError(
                "QbraidEstimate.to_dataframe() requires pandas. "
                "Install it with 'pip install pandas'."
            ) from err

        columns = [
            "deviceQrn",
            "shots",
            "minutes",
            "cost_exact",
            "cost_runtime",
            "cost_total",
            "quality",
            "basis",
        ]
        basis_order = ["computed", "historical-regression", "assumed-default", "unavailable"]
        rows = []
        for point in self.frontier:
            quantities = [
                point.shots,
                point.minutes,
                point.cost.exact,
                point.cost.runtimeDependent,
                point.cost.total,
                point.quality,
            ]
            basis = max((quantity.basis for quantity in quantities), key=basis_order.index)
            rows.append([point.deviceQrn, *(quantity.value for quantity in quantities), basis])
        return pd.DataFrame(rows, columns=columns)

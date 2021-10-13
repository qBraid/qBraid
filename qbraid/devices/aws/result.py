"""BraketResultWrapper Class"""

from typing import Union
import numpy as np

from braket.tasks import GateModelQuantumTaskResult, AnnealingQuantumTaskResult

from qbraid.devices.result import ResultWrapper


class BraketResultWrapper(ResultWrapper):
    """Wrapper class for Amazon Braket result objects."""

    def __init__(self, result: Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult]):
        """Create new Braket result wrapper"""
        super().__init__(result)

    def measurements(self):
        """2d array - row is shot and column is qubit. Default is None. Only available when
        shots > 0. The qubits in `measurements` are the ones in
        `GateModelQuantumTaskResult.measured_qubits`.

        """
        return np.flip(self.vendor_rlo.measurements, 1)

    def measurement_counts(self):
        braket_counts = dict(self.vendor_rlo.measurement_counts)
        qbraid_counts = {}
        for key in braket_counts:
            str_key = "".join(reversed([str(i) for i in key]))
            qbraid_counts[str_key] = braket_counts[key]
        return qbraid_counts

    def data(self):
        """Return the raw data associated with the run/job."""
        try:
            return self.vendor_rlo.data()
        except AttributeError as err:
            raise AttributeError(
                "This method is only available for 'AnnealingQuantumTaskResult' wrapper objects. "
                "Available methods for 'GateModelQuantumTaskResult' wrapper objects include "
                "'measurements' and 'measurement_counts'."
            ) from err


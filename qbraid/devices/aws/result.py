"""BraketGateModelResult Class"""

# https://github.com/aws/amazon-braket-sdk-python/blob/6926c1676dd5b465ef404614a44538c42ee2727d
# /src/braket/tasks/annealing_quantum_task_result.py

from __future__ import annotations

from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult
from numpy import ndarray

from qbraid.devices.result import ResultWrapper


class BraketGateModelResultWrapper(ResultWrapper):
    """Wrapper class for Amazon Braket ``GateModelQuantumTaskResult`` objects."""

    def __init__(self, gate_model_result: GateModelQuantumTaskResult):
        """Create new Braket result wrapper

        Args:
            gate_model_result (GateModelQuantumTaskResult): a Braket ``Result`` object
        """

        # redundant super delegation but might at more functionality later
        super().__init__(gate_model_result)
        self.vendor_rlo = gate_model_result

    @property
    def measurements(self) -> ndarray:
        """2d array - row is shot and column is qubit. Default is None. Only available when
        shots > 0. The qubits in `measurements` are the ones in
        `GateModelQuantumTaskResult.measured_qubits`.
        """
        return self.vendor_rlo.measurements

    def data(self, **kwargs):
        """Return the raw data associated with the run/job."""
        return NotImplementedError

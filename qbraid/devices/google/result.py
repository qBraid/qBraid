"""CirqResultWrapper Class"""

import numpy as np

from cirq.study.result import Result

from qbraid.devices.result import ResultWrapper


class CirqResultWrapper(ResultWrapper):
    """Cirq ``Result`` wrapper class."""

    # pylint: disable=too-few-public-methods
    def __init__(self, result: Result):
        """Create a CirqResultWrapper

        Args:
            result (Result): a Cirq ``Result`` object

        """

        super().__init__(result)

    def measurements(self):
        cirq_meas = self.vendor_rlo.measurements
        marray = np.array([cirq_meas[key].flatten() for key in cirq_meas], dtype="int64")
        qbraid_meas = np.einsum('ji->ij', marray)
        return np.flip(qbraid_meas, 1)

    def measurement_counts(self):
        keys = list(self.vendor_rlo.measurements.keys())
        cirq_counts = dict(self.vendor_rlo.multi_measurement_histogram(keys=keys))
        qbraid_counts = {}
        for key in cirq_counts:
            str_key = "".join(reversed([str(i) for i in key]))
            qbraid_counts[str_key] = cirq_counts[key]
        return qbraid_counts

"""CirqResultWrapper Class"""

# https://github.com/quantumlib/Cirq/blob/504bdbb9bb30249d85ecf7ba199b047150ee33f3/cirq-core/cirq
# /study/result.py

from __future__ import annotations

from cirq.study.result import Result
from pandas import DataFrame

from qbraid.devices.result import ResultWrapper


class CirqResultWrapper(ResultWrapper):
    """Cirq ``Result`` wrapper class."""

    # pylint: disable=too-few-public-methods
    def __init__(self, cirq_result: Result):
        """Create a CirqResultWrapper

        Args:
            cirq_result (Result): a Cirq ``Result`` object

        """

        super().__init__(cirq_result)
        self.vendor_rlo = cirq_result

    def data(self, **kwargs) -> DataFrame:
        """Return a DataFrame with columns as measurement keys, rows as repetitions, and a big
        endian integer for individual measurements. Note that when a numpy array is produced from
        this data frame, Pandas will try to use np.int64 as dtype, but will upgrade to object if
        any value is too large to fit.
        """
        return self.vendor_rlo.data

"""ResultWrapper Class"""

# pylint: disable=too-few-public-methods

from abc import ABC, abstractmethod

from qiskit.visualization import plot_histogram


class ResultWrapper(ABC):
    """Abstract interface for result-like classes.

    Args:
        vendor_rlo: a result-like object

    """

    def __init__(self, vendor_rlo):
        self.vendor_rlo = vendor_rlo

    @abstractmethod
    def measurements(self):
        """Return measurements as list"""

    @abstractmethod
    def measurement_counts(self):
        """Returns the histogram data of the run"""

    def plot_counts(self):
        """Plot histogram of measurement counts"""
        counts = self.measurement_counts()
        return plot_histogram(counts)

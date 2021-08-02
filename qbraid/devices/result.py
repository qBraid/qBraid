"""ResultWrapper Class"""

from abc import ABC, abstractmethod


class ResultWrapper(ABC):
    """Abstract interface for result-like classes.

    Args:
        vendor_rlo: a result-like object

    """

    # pylint: disable=too-few-public-methods
    def __init__(self, vendor_rlo):

        self.vendor_rlo = vendor_rlo

    @abstractmethod
    def data(self, **kwargs):
        """Return the raw data from the run/job."""

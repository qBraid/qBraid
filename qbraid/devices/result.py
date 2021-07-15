from abc import ABC, abstractmethod


class ResultWrapper(ABC):
    def __init__(self, vendor_rlo):
        """Abstract interface for result-like classes.
        Args:
            vendor_rlo: a result-like object
        """

        self.vendor_rlo = vendor_rlo

    @abstractmethod
    def data(self):
        pass

from abc import ABC, abstractmethod
from .utils import supported_packages


class QbraidWrapper(ABC):
    @property
    @abstractmethod
    def package(self):
        pass

    @property
    def supported_packages(self) -> list:
        return supported_packages[self.package]

    @abstractmethod
    def transpile(self):
        pass

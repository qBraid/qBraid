from abc import ABC, abstractmethod
from .utils import supported_packages


class QbraidWrapper(ABC):

    @property
    @abstractmethod
    def package(self) -> str:
        pass

    @property
    def supported_packages(self) -> list:
        return supported_packages[self.package]

    @abstractmethod
    def transpile(self, package: str, *args, **kwargs):
        pass

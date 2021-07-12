from abc import ABC, abstractmethod

from .utils import supported_packages


class AbstractMomentWrapper(ABC):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def package(self):
        pass

    def supported_packages(self):
        return supported_packages[self.package]

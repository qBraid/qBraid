from abc import ABC, abstractmethod


class QbraidTranspiler(ABC):

    @abstractmethod
    def transpile(self, package: str, *args, **kwargs):
        pass

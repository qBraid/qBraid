from typing import Iterable, Union
from abc import ABC
import abc

from .utils import supported_packages

from braket.circuits.moments import Moments as BraketMoments
from cirq.ops.moment import Moment as CirqMoment


class AbstractMomentWrapper(ABC):
    def __init__(self):
        pass

    @property
    @abc.abstractmethod
    def package(self):
        pass

    def supported_packages(self):
        return supported_packages[self.package]

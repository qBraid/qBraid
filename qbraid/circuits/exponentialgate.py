from typing import abstractmethod

from .gate import Gate


class ExponentialGate(Gate):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def exponent(self):
        pass

    @exponent.setter
    @abstractmethod
    def exponent(self, value):
        pass

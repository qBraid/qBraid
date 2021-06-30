from .gate import Gate

from typing import abstractmethod

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
from abc import ABC, abstractmethod
from qbraid.transpiler.circuit import AbstractCircuitWrapper
from typing import Optional


class AbstractDevice(ABC):

    def __init__(self):

        self._name = None
        self._vendor = None

    @property
    def name(self):
        return self._name

    @property
    def vendor(self):
        return self._vendor

    @property
    def device_type(self):
        # either simultator, noise simulator, ion-trap, superconducting
        raise NotImplementedError

    @property
    def calibration_data(self):
        raise NotImplementedError

    @property
    def num_qubits(self):
        raise NotImplementedError

    @property
    def decay_times(self):
        """Returns a dictionatary of qubits with each data"""
        raise NotImplementedError

    @abstractmethod
    def validate_circuit(self):
        """Checks if a qbraid circuit can be run on this device"""
        raise NotImplementedError

    @abstractmethod
    def run(self, circuit: AbstractCircuitWrapper, shots: Optional[int]):
        raise NotImplementedError


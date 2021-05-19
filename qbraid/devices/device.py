import abc
from abc import ABC


class Device(ABC):

    """
    Devices:
    topology (graph)
    T1/T2 times
    description
    unique_id
    vendor_name
    num_qubits
    device_type
    validate_circuit
    calibration_data (dictionary of its own)
    """

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
        return self._num_qubits

    @property
    def decay_times(self):
        """Returns a dictionatary of qubits with each data"""
        raise NotImplementedError

    @abc.abstractmethod
    def validate_circuit(self):
        """Checks if a qbraid circuit can be run on this device"""
        raise NotImplementedError

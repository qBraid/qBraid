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
        self._vendor_name = None

    @property
    def name(self):
        return self._name

    @property
    def vendor_name(self):
        return self._vendor_name

    @property
    def device_type(self):
        # either simultator, noise simulator, ion-trap, superconducting
        pass

    @property
    def calibration_data(self):
        pass

    @property
    def num_qubits(self):
        return self._num_qubits

    @property
    def decay_times(self):
        pass
        # return dictionatary of qubits with each data

    @abc.abstractmethod
    def validate_circuit(self):
        # check if a qbraid circuit can be run on this device
        pass

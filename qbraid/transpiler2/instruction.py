import abc
from abc import ABC

from .outputs import instruction_outputs
from .utils import supported_packages
from qbraid.exceptions import PackageError


class AbstractInstructionWrapper(ABC):
    def __init__(self):

        self.instruction = None
        self.qubits = []

        self.gate = None
        self.params = None

        self._outputs = {}

    @property
    @abc.abstractmethod
    def package(self):
        pass

    @property
    def supported_packages(self):
        return supported_packages[self.package]

    def transpile(self, package: str, output_mapping: dict = None):
        
        if package == self.package:
            return self.circuit
        elif package in self.supported_packages:
            return instruction_outputs[package](self, output_mapping)
        else:
            raise PackageError(f"This instruction cannot be transpiled from {self.package} to {package}.")


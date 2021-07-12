from qbraid.exceptions import PackageError
from .outputs import instruction_outputs
from .wrapper import QbraidWrapper


class InstructionWrapper(QbraidWrapper):
    def __init__(self):

        self.instruction = None
        self.qubits = []

        self.gate = None
        self._params = None

        self._outputs = {}
        self._package = None

    @property
    def params(self):
        return self._params

    @property
    def package(self):
        return self._package

    def transpile(
        self, package: str, output_qubit_mapping: dict = None, output_param_mapping: dict = None
    ):

        if package == self.package:
            return self.instruction
        elif package in self.supported_packages:
            return instruction_outputs[package](self, output_qubit_mapping, output_param_mapping)
        else:
            raise PackageError(f"{package} is not a supported package.")

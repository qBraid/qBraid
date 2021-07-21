from abc import ABC

from .utils import instruction_outputs


class InstructionWrapper(ABC):
    def __init__(self):

        self.instruction = None
        self.qubits = []

        self.gate = None
        self._params = None

    @property
    def params(self):
        return self._params

    def transpile(
        self, package: str, output_qubit_mapping: dict = None, output_param_mapping: dict = None
    ):
        return instruction_outputs[package](self, output_qubit_mapping, output_param_mapping)


from ._utils import instruction_outputs
from .transpiler import QbraidTranspiler


class InstructionWrapper(QbraidTranspiler):
    def __init__(self):

        self.instruction = None
        self.qubits = []

        self.gate = None
        self._params = None

    @property
    def params(self):
        return self._params

    def transpile(self, package, output_qubit_mapping=None, output_param_mapping=None):
        """

        Args:
            package (str):
            output_qubit_mapping (dict):
            output_param_mapping (dict):

        Returns:

        """
        return instruction_outputs[package](self, output_qubit_mapping, output_param_mapping)

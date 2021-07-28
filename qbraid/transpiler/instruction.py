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
        """Return the"""
        return self._params

    def transpile(self, package, output_qubit_mapping=None, output_param_mapping=None):
        """Transpile a qbraid instruction wrapper object to an instruction object of type
         specified by ``package``.

        Args:
            package (str): target package
            output_qubit_mapping (dict): optional qubit mapping
            output_param_mapping (dict): optional parameter mapping

        Returns:
            instruction object of type specified by ``package``.

        """
        return instruction_outputs[package](self, output_qubit_mapping, output_param_mapping)

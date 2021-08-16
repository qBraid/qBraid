from ._utils import instruction_outputs
from .transpiler import QbraidTranspiler


class InstructionWrapper(QbraidTranspiler):
    
    """
    Abstract class for instruction objects. Instructions are objects which 
    store a quantum gate and the qubits applied to that gate. These objects
    may be named differently in various pacakges, but their function is the
    same.

    Attributes:
        params (list): return list of abstract params as :class:`qbraid.transpiler.paramater.ParamID` 
        used within the instruction.
    """

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

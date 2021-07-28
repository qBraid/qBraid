from .transpiler import QbraidTranspiler
from ._utils import moment_outputs

class MomentWrapper(QbraidTranspiler):

    def __init__(self):
        
        self.moment = None
        self.instructions = []

    def transpile(self, package, output_qubit_mapping,output_param_mapping):
        """

        Args:
            package (str):

        Returns:

        """
        return moment_outputs[package](self,output_qubit_mapping,output_param_mapping)

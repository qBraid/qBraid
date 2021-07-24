from ._utils import gate_outputs
from .transpiler import QbraidTranspiler


class GateWrapper(QbraidTranspiler):
    """Abstract Gate wrapper object. Extended by 'QiskitGateWrapper', etc."""

    def __init__(self):
        self.gate = None
        self.name = None
        self.params = []
        self.matrix = None
        self.num_controls = 0
        self.base_gate = None
        self.gate_type = None

    def transpile(self, package, *output_param_mapping):
        """

        Args:
            package (str):
            *output_param_mapping (dict):

        Returns:

        """
        return gate_outputs[package](self, output_param_mapping)

from ._utils import gate_outputs
from .transpiler import QbraidTranspiler


class GateWrapper(QbraidTranspiler):
    """Abstract class for qbraid gate wrapper objects."""

    def __init__(self):
        self.gate = None
        self.name = None
        self.params = []
        self.matrix = None
        self.num_controls = 0
        self.base_gate = None
        self.gate_type = None

    def transpile(self, package, *output_param_mapping):
        """Transpile a qbraid quantum gate wrapper object to quantum gate object of type
         specified by ``package``.

        Args:
            package (str): target package
            *output_param_mapping (dict): optional parameter mapping specification for
                parameterized gates.

        Returns:
            quantum gate object of type specified by ``package``.

        """
        return gate_outputs[package](self, output_param_mapping)

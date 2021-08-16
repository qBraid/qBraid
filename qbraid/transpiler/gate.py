from ._utils import gate_outputs
from .transpiler import QbraidTranspiler


class GateWrapper(QbraidTranspiler):
    """Abstract class for qbraid gate wrapper objects.
    
    Attributes:
        matrix (numpy.ndarray): matrix representing the gate
        name (optional[str]): name of the gate
        gate_type (str): the abstract name of the gate. No matter the way a gate
            is named in the underlying packet, this string follows qbraid's conventions,
            which can be found here.
        num_controls(int): Default is 0. 
        base_gate( :class:`qbraid.transpiler.gate.GateWrapper`): the single- or two-qubit gate being controlled. 
            Defaults to `None`.
        params( list[int,float,ParamID]): all the parameters associated with the gate. These may be abstract parameters
            or simply numbers.
    """

    def __init__(self):
        self.gate = None
        self.name = None
        self.params = []
        self.matrix = None
        self.num_controls = 0
        self.base_gate = None
        self.gate_type = None

    def transpile(self, package, output_param_mapping):
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

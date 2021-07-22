from abc import ABC

from ._utils import gate_outputs


class GateWrapper(ABC):
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
        return gate_outputs[package](self, output_param_mapping)

from qbraid.exceptions import PackageError
from .outputs import gate_outputs
from .wrapper import QbraidWrapper


class GateWrapper(QbraidWrapper):
    """Abstract Gate wrapper object. Extended by 'QiskitGateWrapper', etc."""

    def __init__(self):

        self.gate = None
        self.name = None

        self.params = []
        self.matrix = None

        self.num_controls = 0
        self.base_gate = None

        self._gate_type = None
        self._outputs = {}

    def _add_output(self, package, output):
        self._outputs[package] = output

    @property
    def package(self):
        return None

    def transpile(self, package: str, output_param_mapping):
        """If transpiled object not created, create it. Then return."""

        if package not in self._outputs.keys():

            if package not in self.supported_packages:
                raise PackageError(package)
            output = gate_outputs[package](self, output_param_mapping)
            self._add_output(package, output)

        return self._outputs[package]

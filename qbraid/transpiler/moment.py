from ._utils import moment_outputs
from .transpiler import QbraidTranspiler


class MomentWrapper(QbraidTranspiler):

    """Abstract class for wrapping Moment objects."""

    def __init__(self):
        self.moment = None
        self._instructions = []

    @property
    def instructions(self):
        return self._instructions

    def transpile(self, package, output_qubit_mapping, output_param_mapping):
        """

        Args:
            package (str):

        Returns:

        """
        return moment_outputs[package](self, output_qubit_mapping, output_param_mapping)

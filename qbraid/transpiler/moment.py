"""MomentWrapper Class"""

from qbraid.transpiler._utils import moment_outputs
from qbraid.transpiler.transpiler import QbraidTranspiler


class MomentWrapper(QbraidTranspiler):
    """Abstract class for wrapping Moment objects."""

    def __init__(self):
        self.moment = None
        self._instructions = []

    @property
    def instructions(self):
        """Return the instructions contained within this moment."""
        return self._instructions

    def transpile(self, package, output_qubit_mapping, output_param_mapping):
        """transpile

        Args:
            package (str):

        Returns:

        """
        return moment_outputs[package](self, output_qubit_mapping, output_param_mapping)

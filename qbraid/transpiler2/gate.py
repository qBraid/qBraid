# from braket.circuits.gate import Gate as BraketGate

# from cirq.ops.gate_features import SingleQubitGate as CirqSingleQubitGate
# from cirq.ops.gate_features import ThreeQubitGate as CirqThreeQubitGate
# from cirq.ops.gate_features import TwoQubitGate as CirqTwoQubitGate
# from cirq.ops.measurement_gate import MeasurementGate as CirqMeasure

# from qiskit.circuit.gate import Gate as QiskitGate
# from qiskit.circuit.measure import Measure as QiskitMeasure


from .parameter import ParameterWrapper, ParamID

from .outputs import gate_outputs

from qbraid.exceptions import PackageError

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

    def transpile(self, package: str, output_param_mapping):
        """If transpiled object not created, create it. Then return."""

        if package not in self._outputs.keys():

            if package not in self.supported_packages:
                raise PackageError(package)
            output = gate_outputs[package](self, output_param_mapping)
            self._add_output(package, output)

        return self._outputs[package]

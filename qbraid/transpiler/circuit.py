from abc import abstractmethod

from ._utils import circuit_outputs, supported_packages
from .exceptions import TranspilerError
from .transpiler import QbraidTranspiler


class CircuitWrapper(QbraidTranspiler):
    """Abstract class for qbraid circuit wrapper objects."""
    def __init__(self, circuit, input_qubit_mapping):

        self._circuit = circuit
        self._input_qubit_mapping = input_qubit_mapping
        self._qubits = []
        self._num_qubits = 0
        self._num_clbits = 0
        self._params = []
        self._input_param_mapping = None
        self._package = None

    @property
    @abstractmethod
    def instructions(self):
        """Return an Iterable of instructions in the circuit."""
        pass

    @property
    def circuit(self):
        return self._circuit

    @property
    def qubits(self):
        """Return the qubits acted upon by the operations in this circuit"""
        return self._qubits

    @property
    def num_qubits(self):
        return self._num_qubits

    @property
    def num_clbits(self):
        return self._num_clbits

    @property
    def params(self):
        """Return the circuit parameters. Defaults to None."""
        return self._params

    @property
    def input_param_mapping(self):
        """Return the input parameter mapping. Defaults to None."""
        return self._input_param_mapping

    @property
    def input_qubit_mapping(self):
        """Return the input qubit mapping."""
        if self._input_qubit_mapping is None:
            return {q: i for i, q in enumerate(self.qubits)}
        return self._input_qubit_mapping

    @property
    def package(self):
        """Return the original package of the wrapped circuit."""
        return self._package

    @property
    def supported_packages(self):
        """Return a list of the packages available for transpile."""
        return supported_packages[self.package]

    def transpile(self, package, *args, **kwargs):
        """Transpile a qbraid quantum circuit wrapper object to quantum circuit object of type
         specified by ``package``.

        Args:
            package (str): target package

        Returns:
            quantum circuit object of type specified by ``package``

        """
        if package == self.package:
            return self.circuit
        elif package in self.supported_packages:
            return circuit_outputs[package](self, *args, **kwargs)
        else:
            raise TranspilerError(f"{package} is not a supported package.")

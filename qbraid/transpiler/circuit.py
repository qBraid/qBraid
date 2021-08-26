"""CircuitWrapper Class"""

from abc import abstractmethod

from qbraid.transpiler._utils import circuit_outputs, supported_packages
from qbraid.transpiler.exceptions import TranspilerError
from qbraid.transpiler.transpiler import QbraidTranspiler


class CircuitWrapper(QbraidTranspiler):
    """Abstract class for qbraid circuit wrapper objects.

    Note: The circuit wrapper object keeps track of abstract parameters and qubits using an
    intermediate representation. Qubits are stored simplhy as integers, and abstract parameters
    are stored as a :class:`qbraid.transpiler.parameter.ParamID` object, which stores an index in
    addition to a name. All other objects are transpiled directly when the
    :meth:`qbraid.transpiler.CircuitWrapper.transpile` method is called.

    Attributes:
        instructions (Iterable): list of
            :class:`qbraid.transpiler.instructionwrapper.InstructionWrapper` objects
        moments (Iterable): list of :class:`qbraid.transpiler.momentwrapper.MomentWrapper` objects,
            may be none if package does not support moments
        circuit: the underlying circuit object that has been wrapped
        qubits (List[int]): list of integers which represent all the qubits in the circuit,
            typically stored sequentially
        params: (Iterable): list of abstract paramaters in the circuit, stored as
            :class:`qbraid.transpiler.parameter.ParamID` objects
        num_qubits (int): number of qubits in the circuit
        input_qubit_mapping (dict): dictionary where the keys are qubit objects of the underlying
            circuit and values are integers which track the qubit identity.
        input_param_mapping (dict): dictionary where the keys are abstract parameter objects of the
            underlying circuit and values are :class:`qbraid.transpiler.parameter.ParamID` objects
        package (str): the package with which the underlying circuit was cosntructed

    """

    def __init__(self, circuit, input_qubit_mapping):

        self._circuit = circuit
        self._input_qubit_mapping = input_qubit_mapping
        self._qubits = []
        self._num_qubits = 0
        self._num_clbits = 0
        self._params = []
        self._input_param_mapping = {}
        self._package = None

    @property
    @abstractmethod
    def instructions(self):
        """Return an Iterable of instructions in the circuit."""

    @property
    @abstractmethod
    def moments(self):
        """Return an Iterable of moments in the circuit."""

    @property
    def circuit(self):
        """Return the underlying circuit that has been wrapped."""
        return self._circuit

    @property
    def qubits(self):
        """Return the qubits acted upon by the operations in this circuit"""
        return self._qubits

    @property
    def num_qubits(self):
        """Return the number of qubits in the circuit."""
        return self._num_qubits

    @property
    def num_clbits(self):
        """Return the number of classical bits in the circuit."""
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
        if package in self.supported_packages:
            return circuit_outputs[package](self, *args, **kwargs)
        raise TranspilerError(f"{package} is not a supported package.")

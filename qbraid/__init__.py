"""This top level module contains the main qBraid public functionality."""

# qbraid errors operator
from qbraid.exceptions import QbraidError, PackageError

# The main qbraid operators and functions
from qbraid.circuits import Circuit, UpdateRule
from qbraid.transpiler import CircuitWrapper, qbraid_wrapper
from qbraid.devices import (
    DeviceLikeWrapper,
    JobLikeWrapper,
    ResultWrapper,
    get_devices,
    device_wrapper,
)

from qbraid._version import __version__
from typing import Union

SUPPORTED_CIRCUIT = Union[
    "braket.circuits.circuit.Circuit",
    "cirq.circuits.circuit.Circuit",
    "qiskit.circuit.quantumcircuit.QuantumCircuit",
]


def circuit_wrapper(circuit, **kwargs):
    r"""circuit_wrapper(circuit, input_qubit_mapping=None, **kwargs)
    Load a class :class:`~qbraid.transpiler.CircuitWrapper` and return the instance.

    This function is used to create a qBraid circuit-wrapper object, which can then be transpiled
    to any supported quantum circuit-building package. The input quantum circuit object must be
    an instance of a circuit object derived from a supported package. qBraid comes with support
    for the following input circuit objects and corresponding quantum circuit-building packages:

    * :class:`braket.circuits.circuit.Circuit`: Amazon Braket is a fully
      mamanged AWS service that helps researchers, scientists, and developers get started
      with quantum computing. Amazon Braket provides on-demand access to managed, high-performance
      quantum circuit simulators, as well as different types of quantum computing hardware.

    * :class:`cirq.circuits.circuit.Circuit`: Cirq is a Python library designed by Google
      for writing, manipulating, and optimizing quantum circuits and running them against
      quantum computers and simulators.

    * :class:`qiskit.circuit.quantumcircuit.QuantumCircuit`: Qiskit is an open-source quantum
      software framework designed by IBM. Supported hardware backends include the IBM Quantum
      Experience.

    All circuit-wrapper objects accept an ``input_qubit_mapping`` argument which gives an explicit
    specification for the ordering of qubits. This argument may be needed for transpiling between
    circuit-building packages that do not share equivalent qubit indexing.

    .. code-block:: python

        cirq_circuit = cirq.Circuit()
        q0, q1, q2 = [cirq.LineQubit(i) for i in range(3)]
        input_qubit_mapping = {q0:2,q1:1,q2:0}  # specify a reverse qubit ordering
        ...

    Please refer to the documentation of the individual qbraid circuit wrapper objects to see
    any additional arguments that might be supported.

   Args:
        circuit (SUPPORTED_CIRCUIT): a supported quantum circuit object
        kwargs: keyword arguments including (dict) ``input_qubit_mapping`` which maps each
            qubit object an index as shown above.

    Returns:
        :class:`~qbraid.transpiler.CircuitWrapper`: a package-specific instance of a
            qbraid circuit wrapper.

    """


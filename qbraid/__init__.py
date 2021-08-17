"""This top level module contains the main qBraid public functionality."""


from importlib import reload
from typing import Optional

import pkg_resources

from qbraid._version import __version__
from qbraid.circuits import Circuit, UpdateRule
from qbraid.devices import get_devices
from qbraid.exceptions import QbraidError, WrapperError


def refresh_transpiler():
    global transpiler_entrypoints  # pylint:disable=global-statement
    reload(pkg_resources)
    transpiler_entrypoints = _get_entrypoints("qbraid.transpiler")


def refresh_devices():
    global devices_entrypoints  # pylint:disable=global-statement
    reload(pkg_resources)
    devices_entrypoints = _get_entrypoints("qbraid.devices")


def _get_entrypoints(group: str):
    """Returns a dictionary mapping each entry of ``group`` to its loadable entrypoint."""
    return {entry.name: entry for entry in pkg_resources.iter_entry_points(group)}


transpiler_entrypoints = _get_entrypoints("qbraid.transpiler")
devices_entrypoints = _get_entrypoints("qbraid.devices")


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
        circuit: a supported quantum circuit object

    Keyword Args:
        input_qubit_mapping: dictionary mapping each qubit object to an index

    """
    package = circuit.__module__.split(".")[0]

    if package not in transpiler_entrypoints:
        refresh_transpiler()

    if package in transpiler_entrypoints:
        circuit_wrapper_class = transpiler_entrypoints[package].load()
        return circuit_wrapper_class(circuit, **kwargs)

    raise WrapperError(f"{package} is not a supported package.")


def device_wrapper(device_id: str, **kwargs):
    """Apply qbraid device wrapper to device from a supported device provider.

    Args:
        device_id (str): unique ID specifying a supported quantum hardware device/simulator

    Returns:
        :class:`~qbraid.devices.DeviceLikeWrapper`: a qbraid device wrapper object

    Raises:
        ``WrapperError``: If ``device_id`` is not a valid device reference.
    """
    parse_id = device_id.split("_")
    vendor = parse_id[0]
    provider = parse_id[1]

    if provider == "native":
        provider = vendor

    if vendor not in devices_entrypoints:
        refresh_devices()

    if vendor in devices_entrypoints:
        device_wrapper_class = devices_entrypoints[vendor].load()
        return device_wrapper_class(device_id, provider, **kwargs)

    else:
        raise WrapperError("Invalid device ID")

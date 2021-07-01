from braket.circuits.circuit import Circuit as BraketCircuit
from braket.tasks.quantum_task import QuantumTask as BraketRunResult
from cirq.circuits import Circuit as CirqCircuit
from cirq.study.result import Result as CirqRunResult
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.providers.job import Job as QiskitRunResult

from qbraid.transpiler.transpiler import qbraid_wrapper
from .exceptions import DeviceError
from typing import Union

SupportedCircuit = Union[BraketCircuit, CirqCircuit, QiskitCircuit]
SupportedResult = Union[BraketRunResult, CirqRunResult, QiskitRunResult]


def run(circuit: SupportedCircuit, provider: str, device: str, **options) -> SupportedResult:
    """Run on a device.
    This method that will return a :class:`~qiskit.providers.Job` object
    that run circuits. Depending on the device this may be either an async
    or sync call. It is the discretion of the provider to decide whether
    running should  block until the execution is finished or not. The Job
    class can handle either situation.
    Args:
        circuit (SupportedCircuit): a braket, cirq, or qiskit quantum circuit object
        options: Any kwarg options to pass to the device for running the config. If a key is also
        present in the options attribute/object then the expectation is that the value specified
        will be used instead of what's set in the options object.
    Returns:
        Job: The job object for the run
    """

    if isinstance(device, BraketDevice):
        if not isinstance(circuit, BraketCircuit):
            qbraid_circuit = qbraid_wrapper(circuit)
            circuit = qbraid_circuit.transpile("braket")
            return NotImplemented

    elif isinstance(device, CirqDevice):
        if not isinstance(circuit, CirqCircuit):
            qbraid_circuit = qbraid_wrapper(circuit)
            circuit = qbraid_circuit.transpile("cirq")
            return NotImplemented

    elif isinstance(device, QiskitDevice):
        if not isinstance(circuit, CirqCircuit):
            qbraid_circuit = qbraid_wrapper(circuit)
            circuit = qbraid_circuit.transpile("qiskit")
            return NotImplemented
    else:
        raise DeviceError("{} is not a supported device.".format(device))

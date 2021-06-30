from braket.circuits.circuit import Circuit as BraketCircuit
from braket.devices.device import Device as BraketDevice
from braket.tasks.quantum_task import QuantumTask as BraketRunResult
from cirq.circuits import Circuit as CirqCircuit
from cirq.devices.device import Device as CirqDevice
from cirq.study.result import Result as CirqRunResult
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.providers.backend import Backend as QiskitDevice
from qiskit.providers.job import Job as QiskitRunResult

from qbraid.transpiler.transpiler import qbraid_wrapper
from .exceptions import DeviceError
from typing import Union

SupportedCircuit = Union[BraketCircuit, CirqCircuit, QiskitCircuit]
SupportedDevice = Union[BraketDevice, CirqDevice, QiskitDevice]
SupportedResult = Union[BraketRunResult, CirqRunResult, QiskitRunResult]


def run(circuit: SupportedCircuit, device: SupportedDevice, shots: int) -> SupportedResult:

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

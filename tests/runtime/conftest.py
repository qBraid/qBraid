# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name,import-outside-toplevel

"""
Fixtures imported/defined in this file can be used by any test in this directory
without needing to import them (pytest will automatically discover them).

"""
import random
import textwrap
from typing import Optional

import numpy as np
import pytest

from qbraid.programs import NATIVE_REGISTRY, ExperimentType
from qbraid.runtime import TargetProfile
from qbraid.runtime.native import QbraidDevice, QbraidProvider
from qbraid.runtime.noise import NoiseModelSet
from qbraid.transpiler import Conversion, ConversionGraph, ConversionScheme

from ._resources import (
    DEVICE_DATA_AQUILA,
    DEVICE_DATA_QIR,
    DEVICE_DATA_QUERA_QASM,
    MockClient,
    MockDevice,
)


def _braket_circuit(meas=True):
    """Returns low-depth, one-qubit Braket circuit to be used for testing."""
    import braket.circuits

    circuit = braket.circuits.Circuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    if meas:
        circuit.measure(0)
    return circuit


def _cirq_circuit(meas=True):
    """Returns Low-depth, one-qubit Cirq circuit to be used for testing.
    If ``meas=True``, applies measurement operation to end of circuit."""
    import cirq

    q0 = cirq.GridQubit(0, 0)

    def basic_circuit():
        yield cirq.H(q0)
        yield cirq.Ry(rads=np.pi / 2)(q0)
        if meas:
            yield cirq.measure(q0, key="q0")

    circuit = cirq.Circuit()
    circuit.append(basic_circuit())
    return circuit


def _qiskit_circuit(meas=True):
    """Returns Low-depth, one-qubit Qiskit circuit to be used for testing.
    If ``meas=True``, applies measurement operation to end of circuit."""
    import qiskit

    circuit = qiskit.QuantumCircuit(1, 1) if meas else qiskit.QuantumCircuit(1)
    circuit.h(0)
    circuit.ry(np.pi / 2, 0)
    if meas:
        circuit.measure(0, 0)
    return circuit


@pytest.fixture
def braket_circuit():
    """Returns low-depth, one-qubit Braket circuit to be used for testing."""
    return _braket_circuit()


@pytest.fixture
def qiskit_circuit():
    """Returns low-depth, one-qubit Qiskit circuit to be used for testing."""
    return _qiskit_circuit()


@pytest.fixture
def qasm3_circuit():
    """Returns low-depth, one-qubit QASM3 circuit to be used for testing."""
    qasm = """
    OPENQASM 3.0;
    bit[1] b;
    qubit[1] q;
    h q[0];
    ry(1.5707963267948966) q[0];
    b[0] = measure q[0];
    """
    return textwrap.dedent(qasm).strip()


@pytest.fixture
def run_inputs():
    """Returns list of test circuits for each available native provider."""
    circuits = []
    if "cirq" in NATIVE_REGISTRY:
        circuits.append(_cirq_circuit(meas=False))
    if "qiskit" in NATIVE_REGISTRY:
        circuits.append(_qiskit_circuit(meas=False))
    if "braket" in NATIVE_REGISTRY:
        circuits.append(_braket_circuit(meas=False))
    return circuits


@pytest.fixture
def circuit(request, run_inputs):
    """Return a circuit for testing."""
    index = request.param
    return run_inputs[index]


@pytest.fixture
def run_inputs_meas():
    """Returns list of test circuits for each available native provider."""
    circuits = []
    if "cirq" in NATIVE_REGISTRY:
        circuits.append(_cirq_circuit(meas=True))
    if "qiskit" in NATIVE_REGISTRY:
        circuits.append(_qiskit_circuit(meas=True))
    if "braket" in NATIVE_REGISTRY:
        circuits.append(_braket_circuit(meas=True))
    return circuits


@pytest.fixture
def circuit_meas(request, run_inputs_meas):
    """Return a circuit for testing."""
    index = request.param
    return run_inputs_meas[index]


@pytest.fixture
def device_data_qir():
    """Return a dictionary of device data for the qBraid QIR simulator."""
    return DEVICE_DATA_QIR


@pytest.fixture
def device_data_quera():
    """Return a dictionary of device data for the QuEra QASM simulator."""
    return DEVICE_DATA_QUERA_QASM


@pytest.fixture
def device_data_aquila():
    """Return a dictionary of device data for the QuEra Aquila QPU."""
    return DEVICE_DATA_AQUILA


@pytest.fixture
def valid_qasm2_no_meas() -> str:
    """Returns a valid qasm string."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    h q[0];
    cx q[0],q[1];
    cx q[1],q[0];
    """
    return textwrap.dedent(qasm).strip()


@pytest.fixture
def valid_qasm2():
    """Valid OpenQASM 2 string with measurement."""
    return """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c0[1];
    creg c1[1];
    swap q[0],q[1];
    measure q[0] -> c0[0];
    measure q[1] -> c1[0];
    """


@pytest.fixture
def mock_client():
    """Mock client for testing."""
    return MockClient()


@pytest.fixture
def mock_provider(mock_client):
    """Mock provider for testing."""
    return QbraidProvider(client=mock_client)


@pytest.fixture
def mock_profile():
    """Mock profile for testing."""
    return TargetProfile(
        device_id="qbraid_qir_simulator",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=64,
        program_spec=QbraidProvider._get_program_spec("pyqir", "qbraid_qir_simulator"),
        noise_models=NoiseModelSet.from_iterable(["ideal"]),
    )


@pytest.fixture
def mock_scheme():
    """Mock conversion scheme for testing."""
    conv1 = Conversion("alice", "bob", lambda x: x + 1)
    conv2 = Conversion("bob", "charlie", lambda x: x - 1)
    graph = ConversionGraph(conversions=[conv1, conv2])
    scheme = ConversionScheme(conversion_graph=graph)
    return scheme


@pytest.fixture
def mock_qbraid_device(mock_profile, mock_scheme, mock_client):
    """Mock QbraidDevice for testing."""
    return QbraidDevice(profile=mock_profile, client=mock_client, scheme=mock_scheme)


@pytest.fixture
def mock_basic_device(mock_profile):
    """Generic mock device for testing."""
    return MockDevice(profile=mock_profile)


def _uniform_state_circuit_cirq(num_qubits: Optional[int] = None, measure: Optional[bool] = True):
    """
    Creates a Cirq circuit where all qubits are entangled to uniformly be in
    either |0⟩ or |1⟩ states upon measurement.

    This circuit initializes the first qubit in a superposition state using a
    Hadamard gate and then entangles all other qubits to this first qubit using
    CNOT gates. This ensures all qubits collapse to the same state upon measurement,
    resulting in either all |0⟩s or all |1⟩s uniformly across different executions.

    Args:
        num_qubits (optional, int): The number of qubits in the circuit. If not provided,
                                    a default random number between 10 and 20 is used.
        measure (optional, bool): Whether to measure the qubits at the end of the circuit.

    Returns:
        cirq.Circuit: The resulting circuit where the measurement outcome of all qubits is
                      either all |0⟩s or all |1⟩s.

    Raises:
        ValueError: If the number of qubits provided is less than 1.
    """
    import cirq

    if num_qubits is not None and num_qubits < 1:
        raise ValueError("Number of qubits must be at least 1.")

    num_qubits = num_qubits or random.randint(10, 20)

    qubits = [cirq.LineQubit(i) for i in range(num_qubits)]

    circuit = cirq.Circuit()

    circuit.append(cirq.H(qubits[0]))

    for qubit in qubits[1:]:
        circuit.append(cirq.CNOT(qubits[0], qubit))

    if measure:
        circuit.append(cirq.measure(*qubits, key="result"))

    return circuit


def _uniform_state_circuit_qiskit(num_qubits: Optional[int] = None, measure: Optional[bool] = True):
    """
    Creates a Qiskit circuit where all qubits are entangled to uniformly be in
    either |0⟩ or |1⟩ states upon measurement.

    Args:
        num_qubits (optional, int): The number of qubits in the circuit. If not provided,
            a default random number between 10 and 20 is used.
        measure (optional, bool): Whether to measure the qubits at the end of the circuit.

    Returns:
        QuantumCircuit: The resulting circuit where the measurement outcome of all qubits is
            either all |0⟩s or all |1⟩s.

    Raises:
        ValueError: If the number of qubits provided is less than 1.
    """
    from qiskit import QuantumCircuit

    if num_qubits is not None and num_qubits < 1:
        raise ValueError("Number of qubits must be at least 1.")

    num_qubits = num_qubits or random.randint(10, 20)

    circuit = QuantumCircuit(num_qubits)

    circuit.h(0)

    for qubit in range(1, num_qubits):
        circuit.cx(0, qubit)

    if measure:
        circuit.measure_all()

    return circuit


@pytest.fixture
def cirq_uniform():
    """Cirq circuit used for testing."""
    return _uniform_state_circuit_cirq


@pytest.fixture
def qiskit_uniform():
    """Qiskit circuit used for testing."""
    return _uniform_state_circuit_qiskit


@pytest.fixture
def braket_ahs():
    """Return an example AHS program."""
    import braket.ahs
    import braket.timings

    a = 5.7e-6  # meters

    register = braket.ahs.AtomArrangement()
    register.add(np.array([0.5, 0.5 + 1 / np.sqrt(2)]) * a)
    register.add(np.array([0.5 + 1 / np.sqrt(2), 0.5]) * a)
    register.add(np.array([0.5 + 1 / np.sqrt(2), -0.5]) * a)
    register.add(np.array([0.5, -0.5 - 1 / np.sqrt(2)]) * a)
    register.add(np.array([-0.5, -0.5 - 1 / np.sqrt(2)]) * a)
    register.add(np.array([-0.5 - 1 / np.sqrt(2), -0.5]) * a)
    register.add(np.array([-0.5 - 1 / np.sqrt(2), 0.5]) * a)
    register.add(np.array([-0.5, 0.5 + 1 / np.sqrt(2)]) * a)

    time_max = 4e-6  # seconds
    time_ramp = 1e-7  # seconds
    omega_max = 6300000.0  # rad / sec
    delta_start = -5 * omega_max
    delta_end = 5 * omega_max

    omega = braket.timings.TimeSeries()
    omega.put(0.0, 0.0)
    omega.put(time_ramp, omega_max)
    omega.put(time_max - time_ramp, omega_max)
    omega.put(time_max, 0.0)

    delta = braket.timings.TimeSeries()
    delta.put(0.0, delta_start)
    delta.put(time_ramp, delta_start)
    delta.put(time_max - time_ramp, delta_end)
    delta.put(time_max, delta_end)

    phi = braket.timings.TimeSeries().put(0.0, 0.0).put(time_max, 0.0)

    drive = braket.ahs.DrivingField(amplitude=omega, phase=phi, detuning=delta)

    return braket.ahs.AnalogHamiltonianSimulation(register=register, hamiltonian=drive)


@pytest.fixture
def ahs_dict():
    """Returns dictionary representation of AHS program."""
    return {
        "register": {
            "sites": [
                ["0.00000285", "0.00000688050865276332"],
                ["0.00000688050865276332", "0.00000285"],
                ["0.00000688050865276332", "-0.00000285"],
                ["0.00000285", "-0.00000688050865276332"],
                ["-0.00000285", "-0.00000688050865276332"],
                ["-0.00000688050865276332", "-0.00000285"],
                ["-0.00000688050865276332", "0.00000285"],
                ["-0.00000285", "0.00000688050865276332"],
            ],
            "filling": [1, 1, 1, 1, 1, 1, 1, 1],
        },
        "hamiltonian": {
            "drivingFields": [
                {
                    "amplitude": {
                        "time_series": {
                            "values": ["0.0", "6300000.0", "6300000.0", "0.0"],
                            "times": ["0.0", "1E-7", "0.0000039", "0.000004"],
                        },
                        "pattern": "uniform",
                    },
                    "phase": {
                        "time_series": {"values": ["0.0", "0.0"], "times": ["0.0", "0.000004"]},
                        "pattern": "uniform",
                    },
                    "detuning": {
                        "time_series": {
                            "values": ["-31500000.0", "-31500000.0", "31500000.0", "31500000.0"],
                            "times": ["0.0", "1E-7", "0.0000039", "0.000004"],
                        },
                        "pattern": "uniform",
                    },
                }
            ],
            "localDetuning": [],
        },
    }

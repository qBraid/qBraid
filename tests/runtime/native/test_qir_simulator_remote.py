# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Remote tests for QIR simulator device via qBraid native runtime.

"""

import textwrap

import pyqir
import pytest
from qiskit import QuantumCircuit

from qbraid.programs import ExperimentType
from qbraid.runtime import DeviceStatus, JobStatus, QbraidProvider, TargetProfile
from qbraid.runtime.native import QbraidDevice
from qbraid.runtime.noise import NoiseModelSet

from .._resources import MockClient

DEFAULT_TIMEOUT = 120
DEVICE_ID = "qbraid:qbraid:sim:qir-sv"
SHOTS = 10


@pytest.fixture
def bell_qasm_circuit():
    """Create a Bell state circuit using Qiskit."""
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    return circuit


@pytest.fixture
def bell_qir_module():
    """Create a Bell state circuit as a QIR module."""
    ctx = pyqir.Context()
    mod = pyqir.Module(ctx, "bell_pair")

    entry = pyqir.entry_point(mod, "main", required_num_qubits=2, required_num_results=2)
    builder = pyqir.Builder(ctx)
    builder.insert_at_end(pyqir.BasicBlock(ctx, "entry", entry))

    qis = pyqir.BasicQisBuilder(builder)
    q0 = pyqir.qubit(ctx, 0)
    q1 = pyqir.qubit(ctx, 1)
    r0 = pyqir.result(ctx, 0)
    r1 = pyqir.result(ctx, 1)

    qis.h(q0)
    qis.cx(q0, q1)
    qis.mz(q0, r0)
    qis.mz(q1, r1)

    i8_ptr = pyqir.PointerType(pyqir.IntType(ctx, 8))
    rt_type = pyqir.FunctionType(pyqir.Type.void(ctx), [pyqir.result_type(ctx), i8_ptr])
    rt_fn = pyqir.Function(
        rt_type, pyqir.Linkage.EXTERNAL, "__quantum__rt__result_record_output", mod
    )
    null_i8ptr = pyqir.Constant.null(i8_ptr)
    builder.call(rt_fn, [r0, null_i8ptr])
    builder.call(rt_fn, [r1, null_i8ptr])

    builder.ret(None)
    mod.verify()
    return mod


@pytest.mark.remote
def test_qir_simulator_qasm_circuit(bell_qasm_circuit):
    """Test submitting a QASM circuit to the QIR simulator device."""
    provider = QbraidProvider()
    device = provider.get_device(DEVICE_ID)

    device_status = device.status()
    if device_status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {device_status.value}")

    job = device.run(bell_qasm_circuit, shots=SHOTS)

    try:
        job.wait_for_final_state(timeout=DEFAULT_TIMEOUT)
    except TimeoutError:
        try:
            job.cancel()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        pytest.skip(f"Job did not complete within {DEFAULT_TIMEOUT} seconds")

    assert job.status() == JobStatus.COMPLETED


@pytest.mark.remote
def test_qir_simulator_qir_module(bell_qir_module):
    """Test submitting a QIR module to the QIR simulator device."""
    provider = QbraidProvider()
    device = provider.get_device(DEVICE_ID)

    device_status = device.status()
    if device_status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {device_status.value}")

    job = device.run(bell_qir_module, shots=SHOTS)

    try:
        job.wait_for_final_state(timeout=DEFAULT_TIMEOUT)
    except TimeoutError:
        try:
            job.cancel()
        except Exception:  # pylint: disable=broad-exception-caught
            pass
        pytest.skip(f"Job did not complete within {DEFAULT_TIMEOUT} seconds")

    assert job.status() == JobStatus.COMPLETED


# ---------------------------------------------------------------------------
# Unit tests for QbraidDevice.transform barrier removal
# ---------------------------------------------------------------------------


@pytest.fixture
def qir_device():
    """QbraidDevice configured as a QIR simulator (offline, for unit tests)."""
    profile = TargetProfile(
        device_id=DEVICE_ID,
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=64,
        program_spec=QbraidProvider._get_program_spec("pyqir", DEVICE_ID),
        noise_models=NoiseModelSet.from_iterable(["ideal"]),
    )
    return QbraidDevice(profile=profile, client=MockClient())


@pytest.fixture
def non_qir_device():
    """QbraidDevice configured as a non-QIR device."""
    non_qir_id = "qbraid:qbraid:sim:some-other-device"
    profile = TargetProfile(
        device_id=non_qir_id,
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=64,
        program_spec=QbraidProvider._get_program_spec("pyqir", non_qir_id),
        noise_models=NoiseModelSet.from_iterable(["ideal"]),
    )
    return QbraidDevice(profile=profile, client=MockClient())


@pytest.fixture
def qasm3_with_barrier():
    """OpenQASM 3 program containing a barrier."""
    return textwrap.dedent(
        """
        OPENQASM 3.0;
        qubit[2] q;
        bit[2] b;
        h q[0];
        barrier q[0], q[1];
        cx q[0], q[1];
        b = measure q;
    """
    ).strip()


@pytest.fixture
def qasm3_without_barrier():
    """OpenQASM 3 program without barriers."""
    return textwrap.dedent(
        """
        OPENQASM 3.0;
        qubit[2] q;
        bit[2] b;
        h q[0];
        cx q[0], q[1];
        b = measure q;
    """
    ).strip()


EXPECTED_BELL_NO_BARRIER = (
    "OPENQASM 3.0;\nqubit[2] q;\nbit[2] b;\nh q[0];\ncx q[0], q[1];\nb = measure q;\n"
)


def test_transform_removes_barriers_for_qir_device(qir_device, qasm3_with_barrier):
    """Barriers should be removed when targeting the QIR simulator."""
    result = qir_device.transform(qasm3_with_barrier)
    assert result == EXPECTED_BELL_NO_BARRIER


def test_transform_no_barriers_passthrough(qir_device, qasm3_without_barrier):
    """Programs without barriers should pass through unchanged for QIR devices."""
    result = qir_device.transform(qasm3_without_barrier)
    assert result == qasm3_without_barrier


def test_transform_non_qir_device_preserves_barriers(non_qir_device, qasm3_with_barrier):
    """Non-QIR devices should not strip barriers."""
    result = non_qir_device.transform(qasm3_with_barrier)
    assert result == qasm3_with_barrier


def test_transform_non_qasm_input_passthrough(qir_device):
    """Non-QASM input (e.g. random string) should pass through without error."""
    non_qasm = "this is not a valid quantum program"
    result = qir_device.transform(non_qasm)
    assert result == non_qasm


def test_transform_removes_multiple_barriers(qir_device):
    """Multiple barriers scattered throughout the circuit should all be removed."""
    qasm = textwrap.dedent(
        """
        OPENQASM 3.0;
        qubit[3] q;
        bit[3] b;
        h q[0];
        barrier q[0], q[1], q[2];
        cx q[0], q[1];
        barrier q[1], q[2];
        cx q[1], q[2];
        barrier q[0], q[1], q[2];
        b = measure q;
    """
    ).strip()
    expected = (
        "OPENQASM 3.0;\nqubit[3] q;\nbit[3] b;\n"
        "h q[0];\ncx q[0], q[1];\ncx q[1], q[2];\nb = measure q;\n"
    )
    result = qir_device.transform(qasm)
    assert result == expected


def test_transform_removes_barrier_on_single_qubit(qir_device):
    """A barrier applied to a single qubit should be removed."""
    qasm = textwrap.dedent(
        """
        OPENQASM 3.0;
        qubit[1] q;
        bit[1] b;
        h q[0];
        barrier q[0];
        b[0] = measure q[0];
    """
    ).strip()
    expected = "OPENQASM 3.0;\nqubit[1] q;\nbit[1] b;\nh q[0];\nb[0] = measure q[0];\n"
    result = qir_device.transform(qasm)
    assert result == expected


def test_transform_removes_barrier_between_measurements(qir_device):
    """Barrier placed between gate operations and measurements should be removed."""
    qasm = textwrap.dedent(
        """
        OPENQASM 3.0;
        qubit[2] q;
        bit[2] b;
        h q[0];
        cx q[0], q[1];
        barrier q[0], q[1];
        b = measure q;
    """
    ).strip()
    result = qir_device.transform(qasm)
    assert result == EXPECTED_BELL_NO_BARRIER


def test_transform_barrier_only_circuit(qir_device):
    """A circuit that is just gates and a barrier (no measurement) should have barrier stripped."""
    qasm = textwrap.dedent(
        """
        OPENQASM 3.0;
        qubit[2] q;
        h q[0];
        barrier q[0], q[1];
        cx q[0], q[1];
    """
    ).strip()
    expected = "OPENQASM 3.0;\nqubit[2] q;\nh q[0];\ncx q[0], q[1];\n"
    result = qir_device.transform(qasm)
    assert result == expected
